package main

import (
	"fmt"
	"log"
	"net/http"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(`{"service":"order-service-go","status":"healthy"}`))
	})

	addr := ":8083"
	fmt.Printf("order-service-go listening on %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, r))
}
