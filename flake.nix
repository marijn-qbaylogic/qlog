{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { nixpkgs, flake-utils, pyproject-nix, uv2nix, pyproject-build-systems, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system};
          inherit (nixpkgs) lib;
          inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;
          python = pkgs.python3;
          workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
          overlays = [
            pyproject-build-systems.overlays.wheel
            (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
          ];
          set0 = pkgs.callPackage pyproject-nix.build.packages { inherit python; };
          set = set0.overrideScope (lib.composeManyExtensions overlays);
          venv = set.mkVirtualEnv "app-venv" workspace.deps.default;
          app = mkApplication {
            inherit venv;
            package = set.qlog;
          };
      in {
        packages.default = app;
        devShells.uv = pkgs.mkShell {
          packages = [
            pkgs.uv
          ];
          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = python.interpreter;
            UV_PYTHON_DOWNLOADS = "never";
          };
          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel)
          '';
        };
        devShells.default = pkgs.mkShell {
          packages = [
            venv
            pkgs.uv
          ];
          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = set.python.interpreter;
            UV_PYTHON_DOWNLOADS = "never";
          };
          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel)
          '';
        };
      }
    );
}
