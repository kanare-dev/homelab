package checker

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"time"

	"lab/config"
)

type Result struct {
	Host    string
	Service string
	Status  string
}

const timeout = 3 * time.Second

func Check(ctx context.Context, cfg *config.Config) ([]Result, error) {
	var results []Result
	for hostName, host := range cfg.Hosts {
		for _, svc := range host.Services {
			status := checkService(ctx, host.IP, &svc)
			results = append(results, Result{
				Host:    hostName,
				Service: svc.Name,
				Status:  status,
			})
		}
	}
	return results, nil
}

func checkService(ctx context.Context, ip string, svc *config.Service) string {
	switch svc.Check {
	case "tcp":
		return checkTCP(ctx, ip, svc.Port)
	case "udp":
		return checkUDP(ctx, ip, svc.Port)
	case "http":
		return checkHTTP(ctx, svc.URL)
	case "ssh":
		return checkSSH(ctx, ip, svc.Command)
	default:
		return "UNKNOWN"
	}
}

func checkTCP(ctx context.Context, ip string, port int) string {
	addr := fmt.Sprintf("%s:%d", ip, port)
	d := net.Dialer{Timeout: timeout}
	conn, err := d.DialContext(ctx, "tcp", addr)
	if err != nil {
		return "DOWN"
	}
	conn.Close()
	return "UP"
}

func checkUDP(ctx context.Context, ip string, port int) string {
	addr := fmt.Sprintf("%s:%d", ip, port)
	d := net.Dialer{Timeout: timeout}
	conn, err := d.DialContext(ctx, "udp", addr)
	if err != nil {
		return "DOWN"
	}
	conn.Close()
	return "UP"
}

func checkSSH(ctx context.Context, ip string, command string) string {
	home, _ := os.UserHomeDir()
	cmd := exec.CommandContext(ctx, "ssh",
		"-o", "ConnectTimeout=3",
		"-o", "StrictHostKeyChecking=no",
		"-o", "BatchMode=yes",
		"-i", home+"/.ssh/id_ed25519_homelab",
		"ubuntu@"+ip,
		command,
	)
	if err := cmd.Run(); err != nil {
		return "DOWN"
	}
	return "UP"
}

func checkHTTP(ctx context.Context, url string) string {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return "DOWN"
	}
	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)
	if err != nil {
		return "DOWN"
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 200 && resp.StatusCode < 400 {
		return "UP"
	}
	return "DOWN"
}
