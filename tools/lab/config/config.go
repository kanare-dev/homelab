package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Hosts map[string]Host `yaml:"hosts"`
}

type Host struct {
	IP       string    `yaml:"ip"`
	Services []Service `yaml:"services"`
}

type Service struct {
	Name    string `yaml:"name"`
	Check   string `yaml:"check"` // tcp, udp, http, ssh
	Port    int    `yaml:"port"`
	URL     string `yaml:"url"`
	Command string `yaml:"command"` // ssh check で実行するコマンド
}

func Load(path string) (*Config, error) {
	if path == "" {
		var err error
		path, err = findConfig()
		if err != nil {
			return nil, err
		}
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("parse config: %w", err)
	}
	return &cfg, nil
}

func findConfig() (string, error) {
	if p := os.Getenv("LAB_CONFIG"); p != "" {
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}
	// 1. カレントディレクトリ
	if wd, err := os.Getwd(); err == nil {
		for _, p := range []string{
			filepath.Join(wd, "lab.yaml"),
			filepath.Join(wd, "lab", "lab.yaml"),
			filepath.Join(wd, "tools", "lab", "lab.yaml"),
		} {
			if _, err := os.Stat(p); err == nil {
				return p, nil
			}
		}
	}
	// 2. lab バイナリと同じディレクトリ
	if exec, err := os.Executable(); err == nil {
		p := filepath.Join(filepath.Dir(exec), "lab.yaml")
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}
	// 3. ~/.config/homelab/lab.yaml
	home, _ := os.UserHomeDir()
	p := filepath.Join(home, ".config", "homelab", "lab.yaml")
	if _, err := os.Stat(p); err == nil {
		return p, nil
	}
	return "", fmt.Errorf("lab.yaml が見つかりません。-c でパスを指定するか、上記のいずれかに配置してください")
}
