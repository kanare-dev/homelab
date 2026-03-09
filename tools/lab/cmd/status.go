package cmd

import (
	"context"
	"fmt"

	"github.com/spf13/cobra"

	"lab/checker"
	"lab/config"
)

var (
	configPath string
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "VM とサービスの状態を表示",
	RunE:  runStatus,
}

func init() {
	rootCmd.AddCommand(statusCmd)
	statusCmd.Flags().StringVarP(&configPath, "config", "c", "", "設定ファイルのパス")
}

func runStatus(cmd *cobra.Command, args []string) error {
	cfg, err := config.Load(configPath)
	if err != nil {
		return fmt.Errorf("設定の読み込み: %w", err)
	}

	ctx := context.Background()
	results, err := checker.Check(ctx, cfg)
	if err != nil {
		return err
	}

	printTable(results)
	return nil
}

func printTable(results []checker.Result) {
	// ヘッダー
	fmt.Printf("%-20s %-20s %-10s\n", "NAME", "SERVICE", "STATUS")
	fmt.Printf("%-20s %-20s %-10s\n", "----", "-------", "------")

	for _, r := range results {
		status := r.Status
		if r.Status == "UP" {
			status = "UP"
		} else if r.Status == "DOWN" {
			status = "DOWN"
		}
		fmt.Printf("%-20s %-20s %-10s\n", r.Host, r.Service, status)
	}
}
