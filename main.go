package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"

	"github.com/rchapin/backup_manager/run"
)

func main() {
	fmt.Println(os.Args)
	ctx, cancel := context.WithCancel(context.Background())
	err := run.Run(os.Args, ctx, cancel)
	if err != nil {
		slog.Error(
			"executing run.Run",
			slog.String("err", err.Error()),
		)
		os.Exit(1)
	}
}
