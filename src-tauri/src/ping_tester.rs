use std::collections::HashMap;
use std::net::SocketAddr;
use std::time::{Duration, Instant, SystemTime};
use tokio::net::UdpSocket;

/// Constructs a standard RFC 1035 DNS Query packet for type A (IPv4).
fn build_dns_query_packet(domain: &str, tx_id: u16) -> Vec<u8> {
    let mut packet = Vec::with_capacity(64);
    // Transaction ID (2 bytes)
    packet.push((tx_id >> 8) as u8);
    packet.push((tx_id & 0xFF) as u8);
    // Flags: 0x0100 (Standard query with Recursion Desired)
    packet.push(0x01);
    packet.push(0x00);
    // QDCOUNT (Questions): 1
    packet.push(0x00);
    packet.push(0x01);
    // ANCOUNT: 0
    packet.push(0x00);
    packet.push(0x00);
    // NSCOUNT: 0
    packet.push(0x00);
    packet.push(0x00);
    // ARCOUNT: 0
    packet.push(0x00);
    packet.push(0x00);

    for label in domain.split('.') {
        if label.is_empty() {
            continue;
        }
        let bytes = label.as_bytes();
        packet.push(bytes.len() as u8);
        packet.extend_from_slice(bytes);
    }
    packet.push(0x00); // Root label null terminator

    // QTYPE: 0x0001 (A record)
    packet.push(0x00);
    packet.push(0x01);
    // QCLASS: 0x0001 (IN)
    packet.push(0x00);
    packet.push(0x01);

    packet
}

/// Measures real DNS query Round-Trip Time (RTT) in milliseconds using UDP on port 53.
/// Returns Ok(latency_ms) on success, or Err("Timeout") on failure.
pub async fn test_dns_ip_latency(dns_ip: &str, timeout_ms: u64) -> Result<i64, String> {
    let target_addr: SocketAddr = format!("{}:53", dns_ip.trim())
        .parse()
        .map_err(|e| format!("Invalid DNS IP address: {}", e))?;

    let socket = UdpSocket::bind("0.0.0.0:0")
        .await
        .map_err(|e| format!("Failed to bind local UDP socket: {}", e))?;

    // Randomized 16-bit Transaction ID
    let now = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap_or_default();
    let tx_id = ((now.as_micros() ^ (std::process::id() as u128)) & 0xFFFF) as u16;

    let packet = build_dns_query_packet("google.com", tx_id);
    let start = Instant::now();

    tokio::time::timeout(Duration::from_millis(timeout_ms), async {
        socket
            .send_to(&packet, target_addr)
            .await
            .map_err(|e| format!("Failed to send UDP packet: {}", e))?;

        let mut buf = [0u8; 512];
        loop {
            let (len, from_addr) = socket
                .recv_from(&mut buf)
                .await
                .map_err(|e| format!("Socket receive error: {}", e))?;

            if len >= 12 && from_addr.ip() == target_addr.ip() {
                let resp_id = ((buf[0] as u16) << 8) | (buf[1] as u16);
                if resp_id == tx_id {
                    let rtt = start.elapsed().as_millis() as i64;
                    return Ok(rtt);
                }
            }
        }
    })
    .await
    .map_err(|_| "Timeout".to_string())?
}

/// Concurrently tests all DNS servers in the list.
/// Returns a map of id -> latency_ms where >= 0 is RTT, and -1 represents Timeout/Offline.
pub async fn bulk_test_dns_latencies(
    dns_servers: Vec<(String, String)>, // (id, primary_ip)
    timeout_ms: u64,
) -> HashMap<String, i64> {
    let mut handles = Vec::new();

    for (id, ip) in dns_servers {
        handles.push(tauri::async_runtime::spawn(async move {
            let latency = match test_dns_ip_latency(&ip, timeout_ms).await {
                Ok(ms) => ms,
                Err(_) => -1, // -1 means Timeout
            };
            (id, latency)
        }));
    }

    let mut results = HashMap::new();
    for handle in handles {
        if let Ok((id, latency)) = handle.await {
            results.insert(id, latency);
        }
    }

    results
}
