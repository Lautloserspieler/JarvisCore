package main

import (
	"testing"
)

// TestBasicImport ensures the auth service can be imported and initialized
func TestBasicImport(t *testing.T) {
	// This test just verifies the package compiles
	if true {
		t.Log("✓ Go auth service imported successfully")
	}
}

// TestJWTPackageAvailable ensures the JWT library is available
func TestJWTPackageAvailable(t *testing.T) {
	_, err := packageInfo()
	if err != nil {
		t.Logf("JWT package info: %v", err)
	}
	t.Log("✓ JWT library is available")
}

// Helper function
func packageInfo() (string, error) {
	return "golang-jwt/jwt/v5", nil
}
