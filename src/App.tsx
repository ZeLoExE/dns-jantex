import React, { useEffect, useState, useMemo } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import {
  ActiveNetworkInfo,
  AppData,
  DnsServer,
  NetworkProfile,
  AppSettings,
  UpdateInfo,
  CaptivePortalEvent,
  ProfileAppliedEvent,
} from "./types";
import { StatusBar } from "./components/StatusBar";
import { SearchAndFilter } from "./components/SearchAndFilter";
import { DnsCard } from "./components/DnsCard";
import { CustomDnsModal } from "./components/CustomDnsModal";
import { ProfilesDrawer } from "./components/ProfilesDrawer";
import { TitleBar } from "./components/TitleBar";
import { Shield, CheckCircle, AlertCircle, Info } from "lucide-react";

export const App: React.FC = () => {
  // Application Data & State
  const [network, setNetwork] = useState<ActiveNetworkInfo | null>(null);
  const [dnsList, setDnsList] = useState<DnsServer[]>([]);
  const [profiles, setProfiles] = useState<NetworkProfile[]>([]);
  const [settings, setSettings] = useState<AppSettings>({
    auto_flush: true,
    start_minimized: false,
    auto_apply_profiles: true,
    captive_portal_guard: true,
    skipped_version: null,
  });

  // UI States
  const [isAdmin, setIsAdmin] = useState(true);
  const [captivePortalAlert, setCaptivePortalAlert] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [isProfilesDrawerOpen, setIsProfilesDrawerOpen] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);

  // Loading & In-Progress States
  const [loadingDhcp, setLoadingDhcp] = useState(false);
  const [loadingFlush, setLoadingFlush] = useState(false);
  const [isPingingAll, setIsPingingAll] = useState(false);
  const [pingingIds, setPingingIds] = useState<Record<string, boolean>>({});
  const [applyingId, setApplyingId] = useState<string | null>(null);

  // Toast Notification System
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (message: string, type: "success" | "error" | "info" = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Initial Data Fetch & Event Listeners
  useEffect(() => {
    const initApp = async () => {
      try {
        const netInfo = await invoke<ActiveNetworkInfo>("get_active_network");
        setNetwork(netInfo);
      } catch (err) {
        console.error("Failed to load network info:", err);
      }

      try {
        const appData = await invoke<AppData>("get_app_data");
        setDnsList(appData.dns_list);
        setProfiles(appData.network_profiles);
        setSettings(appData.settings);
      } catch (err) {
        console.error("Failed to load app data:", err);
      }

      try {
        const adminStatus = await invoke<boolean>("is_admin_elevated");
        setIsAdmin(adminStatus);
      } catch (err) {
        console.error("Failed to check admin elevation:", err);
      }

      try {
        const update = await invoke<UpdateInfo | null>("check_for_updates");
        if (update) setUpdateInfo(update);
      } catch (err) {
        console.warn("Update check ignored:", err);
      }
    };

    initApp();

    // Setup Tauri Event Listeners
    const unlistenNetwork = listen<ActiveNetworkInfo>("network_status_updated", (event) => {
      setNetwork(event.payload);
    });

    const unlistenCaptive = listen<CaptivePortalEvent>("captive_portal_status", (event) => {
      if (event.payload.is_captive) {
        setCaptivePortalAlert(event.payload.message);
      } else {
        setCaptivePortalAlert(null);
      }
    });

    const unlistenProfile = listen<ProfileAppliedEvent>("profile_applied", (event) => {
      showToast(
        `Smart Profile auto-applied: ${event.payload.dns_name} on ${event.payload.network_identifier}`,
        "success"
      );
      invoke<ActiveNetworkInfo>("get_active_network").then(setNetwork);
    });

    return () => {
      unlistenNetwork.then((f) => f());
      unlistenCaptive.then((f) => f());
      unlistenProfile.then((f) => f());
    };
  }, []);

  // Filtered & Sorted DNS Servers (Favorites always pinned on top)
  const filteredDnsList = useMemo(() => {
    return dnsList
      .filter((dns) => {
        // Category filter
        if (selectedCategory === "★ Favorites") {
          if (!dns.is_favorite) return false;
        } else if (selectedCategory === "Gaming") {
          if (!dns.tags.some((t) => /gaming|game/i.test(t))) return false;
        } else if (selectedCategory === "Bypass / Anti-Sanction") {
          if (!dns.tags.some((t) => /bypass|sanction|anti/i.test(t))) return false;
        } else if (selectedCategory === "AdBlock & Security") {
          if (!dns.tags.some((t) => /adblock|security|family/i.test(t))) return false;
        } else if (selectedCategory === "Global") {
          if (!dns.tags.some((t) => /global|fast|reliable|privacy/i.test(t))) return false;
        } else if (selectedCategory === "Custom") {
          if (!dns.id.startsWith("custom_") && !dns.tags.includes("Custom")) return false;
        }

        // Search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim();
          const matchName = dns.name.toLowerCase().includes(q);
          const matchPrimary = dns.primary_ip.includes(q);
          const matchSecondary = dns.secondary_ip.includes(q);
          const matchTags = dns.tags.some((t) => t.toLowerCase().includes(q));
          return matchName || matchPrimary || matchSecondary || matchTags;
        }

        return true;
      })
      .sort((a, b) => {
        if (a.is_favorite !== b.is_favorite) {
          return a.is_favorite ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
  }, [dnsList, selectedCategory, searchQuery]);

  // Active DNS Server Matcher: matches primary (and secondary if configured)
  const isDnsActive = (dns: DnsServer): boolean => {
    if (!network || network.dhcp_enabled || !network.current_dns || network.current_dns.length === 0) {
      return false;
    }
    const currentPrimary = network.current_dns[0]?.trim();
    const currentSecondary = network.current_dns[1]?.trim();

    if (currentPrimary && currentPrimary === dns.primary_ip.trim()) {
      if (dns.secondary_ip && currentSecondary) {
        return currentSecondary === dns.secondary_ip.trim();
      }
      return true;
    }
    return false;
  };

  // Actions
  const handleApplyDns = async (dns: DnsServer) => {
    if (!network?.adapter_name || network.adapter_name === "Disconnected") {
      showToast("No active network adapter found to apply DNS.", "error");
      return;
    }

    setApplyingId(dns.id);
    try {
      await invoke("apply_dns", {
        adapterName: network.adapter_name,
        dnsId: dns.id,
      });

      showToast(`Applied ${dns.name} successfully!`, "success");

      const updatedNet = await invoke<ActiveNetworkInfo>("get_active_network");
      setNetwork(updatedNet);
    } catch (err) {
      showToast(`Failed to apply DNS: ${err}`, "error");
    } finally {
      setApplyingId(null);
    }
  };

  const handleResetDhcp = async () => {
    if (!network?.adapter_name) return;
    setLoadingDhcp(true);
    try {
      await invoke("reset_dhcp", { adapterName: network.adapter_name });
      showToast("Network adapter reverted to automatic DHCP DNS.", "success");
      const updatedNet = await invoke<ActiveNetworkInfo>("get_active_network");
      setNetwork(updatedNet);
    } catch (err) {
      showToast(`Failed to reset to DHCP: ${err}`, "error");
    } finally {
      setLoadingDhcp(false);
    }
  };

  const handleFlushCache = async () => {
    setLoadingFlush(true);
    try {
      await invoke("flush_dns");
      showToast("Windows DNS resolver cache flushed successfully.", "success");
    } catch (err) {
      showToast(`Flush DNS failed: ${err}`, "error");
    } finally {
      setLoadingFlush(false);
    }
  };

  const handleToggleAutoFlush = async () => {
    const newSettings = { ...settings, auto_flush: !settings.auto_flush };
    setSettings(newSettings);
    try {
      await invoke("save_settings", { settings: newSettings });
    } catch (err) {
      console.error("Failed to save settings:", err);
    }
  };

  const handleToggleFavorite = async (id: string) => {
    try {
      const newStatus = await invoke<boolean>("toggle_favorite", { id });
      setDnsList((prev) =>
        prev.map((d) => (d.id === id ? { ...d, is_favorite: newStatus } : d))
      );
    } catch (err) {
      showToast(`Failed to update favorite: ${err}`, "error");
    }
  };

  const handlePingSingle = async (dnsId: string) => {
    setPingingIds((prev) => ({ ...prev, [dnsId]: true }));
    try {
      const latency = await invoke<number>("ping_dns", { dnsId });
      setDnsList((prev) =>
        prev.map((d) => (d.id === dnsId ? { ...d, latency_ms: latency } : d))
      );
      if (latency === -1) {
        showToast("DNS server query timed out (Offline or Filtered).", "info");
      }
    } catch (err) {
      setDnsList((prev) =>
        prev.map((d) => (d.id === dnsId ? { ...d, latency_ms: -1 } : d))
      );
      showToast(`Ping timeout/offline: ${err}`, "info");
    } finally {
      setPingingIds((prev) => ({ ...prev, [dnsId]: false }));
    }
  };

  const handlePingAll = async () => {
    setIsPingingAll(true);
    try {
      const results = await invoke<Record<string, number>>("ping_all_dns");
      setDnsList((prev) =>
        prev.map((d) =>
          results[d.id] !== undefined
            ? { ...d, latency_ms: results[d.id] }
            : d
        )
      );
      showToast("Ping latency testing completed for all servers.", "success");
    } catch (err) {
      showToast(`Failed to test all DNS latencies: ${err}`, "error");
    } finally {
      setIsPingingAll(false);
    }
  };

  const handleSaveCustomDns = async (newDns: DnsServer, applyNow: boolean) => {
    try {
      await invoke("save_dns_server", { server: newDns });
      setDnsList((prev) => [...prev, newDns]);
      showToast(`Added custom DNS: ${newDns.name}`, "success");

      if (applyNow && network?.adapter_name) {
        handleApplyDns(newDns);
      }
    } catch (err) {
      showToast(`Failed to save custom DNS: ${err}`, "error");
    }
  };

  const handleDeleteDns = async (id: string) => {
    try {
      await invoke("delete_dns_server", { id });
      setDnsList((prev) => prev.filter((d) => d.id !== id));
      showToast("Custom DNS removed.", "info");
    } catch (err) {
      showToast(`Failed to delete DNS: ${err}`, "error");
    }
  };

  const handleSaveProfile = async (profile: NetworkProfile) => {
    try {
      await invoke("save_network_profile", { profile });
      setProfiles((prev) => {
        const idx = prev.findIndex((p) => p.id === profile.id);
        if (idx >= 0) {
          const updated = [...prev];
          updated[idx] = profile;
          return updated;
        }
        return [...prev, profile];
      });
      showToast(`Rule saved for network "${profile.network_identifier}"`, "success");
    } catch (err) {
      showToast(`Failed to save network profile: ${err}`, "error");
    }
  };

  const handleDeleteProfile = async (id: string) => {
    try {
      await invoke("delete_network_profile", { id });
      setProfiles((prev) => prev.filter((p) => p.id !== id));
      showToast("Network rule deleted.", "info");
    } catch (err) {
      showToast(`Failed to delete profile: ${err}`, "error");
    }
  };

  const handleUpdateSettings = async (newSettings: AppSettings) => {
    setSettings(newSettings);
    try {
      await invoke("save_settings", { settings: newSettings });
    } catch (err) {
      console.error("Failed to save settings:", err);
    }
  };

  const handleUpdateNow = async () => {
    if (updateInfo) {
      if (updateInfo.download_url) {
        showToast("Downloading update... Please wait.", "info");
        try {
          await invoke("install_update", { downloadUrl: updateInfo.download_url });
        } catch (err) {
          showToast(`Direct update failed: ${err}. Opening release page...`, "error");
          invoke("open_external_url", { url: updateInfo.release_url });
        }
      } else {
        invoke("open_external_url", { url: updateInfo.release_url });
      }
    }
  };

  const handleSkipVersion = async () => {
    if (updateInfo) {
      try {
        await invoke("skip_update_version", {
          version: updateInfo.latest_version,
        });
        setUpdateInfo(null);
        showToast(`Skipped update notifications for v${updateInfo.latest_version}`, "info");
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0b0f19] text-slate-100 select-none rounded-xl border border-slate-800/80 shadow-2xl">
      {/* Custom Frameless Windows Titlebar */}
      <TitleBar
        updateInfo={updateInfo}
        onUpdateNow={handleUpdateNow}
        onDismissUpdate={handleSkipVersion}
      />

      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed top-12 right-4 z-50 flex items-center gap-2 px-3.5 py-2 rounded-xl shadow-2xl text-xs font-medium border backdrop-blur-md animate-in slide-in-from-top-3 duration-200 ${
            toast.type === "success"
              ? "bg-emerald-500/20 text-emerald-200 border-emerald-500/40"
              : toast.type === "error"
              ? "bg-rose-500/20 text-rose-200 border-rose-500/40"
              : "bg-indigo-500/20 text-indigo-200 border-indigo-500/40"
          }`}
        >
          {toast.type === "success" && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
          {toast.type === "error" && <AlertCircle className="w-3.5 h-3.5 text-rose-400" />}
          {toast.type === "info" && <Info className="w-3.5 h-3.5 text-indigo-400" />}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Main Viewport Container */}
      <main className="flex flex-col flex-1 px-3.5 pt-2 pb-2.5 gap-2 w-full min-h-0 overflow-hidden">
        {/* Top Status Bar (Sticky / Non-scrolling) */}
        <div className="shrink-0">
          <StatusBar
            network={network}
            isAdmin={isAdmin}
            captivePortalAlert={captivePortalAlert}
            autoFlush={settings.auto_flush}
            onToggleAutoFlush={handleToggleAutoFlush}
            onResetDhcp={handleResetDhcp}
            onFlushCache={handleFlushCache}
            onOpenProfiles={() => setIsProfilesDrawerOpen(true)}
            loadingDhcp={loadingDhcp}
            loadingFlush={loadingFlush}
          />
        </div>

        {/* Search, Filter & Action Bar (Sticky / Non-scrolling) */}
        <div className="shrink-0">
          <SearchAndFilter
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            onPingAll={handlePingAll}
            isPingingAll={isPingingAll}
            onOpenCustomModal={() => setIsCustomModalOpen(true)}
          />
        </div>

        {/* DNS Server Cards 2-Column Grid / Only Scrollable Area */}
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden pr-1">
          {filteredDnsList.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-xs gap-2 border border-dashed border-slate-800 rounded-2xl">
              <Shield className="w-8 h-8 opacity-40 text-slate-400" />
              <span>No DNS servers match your search criteria.</span>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2.5 pb-1">
              {filteredDnsList.map((dns) => (
                <DnsCard
                  key={dns.id}
                  dns={dns}
                  isActive={isDnsActive(dns)}
                  onApply={handleApplyDns}
                  onToggleFavorite={handleToggleFavorite}
                  onPing={handlePingSingle}
                  onDelete={
                    dns.id.startsWith("custom_")
                      ? () => handleDeleteDns(dns.id)
                      : undefined
                  }
                  isPinging={!!pingingIds[dns.id]}
                  isApplying={applyingId === dns.id}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Add Custom DNS Modal */}
      <CustomDnsModal
        isOpen={isCustomModalOpen}
        onClose={() => setIsCustomModalOpen(false)}
        onSave={handleSaveCustomDns}
      />

      {/* Smart Profiles Drawer */}
      <ProfilesDrawer
        isOpen={isProfilesDrawerOpen}
        onClose={() => setIsProfilesDrawerOpen(false)}
        currentNetworkId={network?.network_identifier || "Wi-Fi"}
        dnsList={dnsList}
        profiles={profiles}
        settings={settings}
        onSaveProfile={handleSaveProfile}
        onDeleteProfile={handleDeleteProfile}
        onUpdateSettings={handleUpdateSettings}
      />
    </div>
  );
};

export default App;
