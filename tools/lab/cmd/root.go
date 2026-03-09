package cmd

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "lab",
	Short: "homelab 監視 CLI",
	Long:  "VM とサービスの状態を確認する homelab 監視ツール",
}

func Execute() error {
	return rootCmd.Execute()
}
