"""Scaffold a Vite + React + Tailwind project from generated components."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent

from strands import tool

from src.tools._validate import safe_component_name, safe_project_name

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
NODE_MODULES_CACHE = Path("/tmp/design-agent-cache/node_modules")
LOCK_CACHE = Path("/tmp/design-agent-cache/package-lock.json")
# Bump when dependencies change to invalidate cached node_modules
_CACHE_VERSION = "2"
_CACHE_VERSION_FILE = Path("/tmp/design-agent-cache/.cache-version")


def _cache_version_matches() -> bool:
    if not _CACHE_VERSION_FILE.is_file():
        return False
    return _CACHE_VERSION_FILE.read_text().strip() == _CACHE_VERSION


def _clear_cache() -> None:
    cache_dir = NODE_MODULES_CACHE.parent
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir)


def _save_cache(project_path: Path) -> None:
    cache_dir = NODE_MODULES_CACHE.parent
    cache_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(project_path / "node_modules", NODE_MODULES_CACHE, symlinks=True)
    lock = project_path / "package-lock.json"
    if lock.is_file():
        shutil.copy2(lock, LOCK_CACHE)
    _CACHE_VERSION_FILE.write_text(_CACHE_VERSION)


@tool
def scaffold_react_app(
    project_name: str,
    components: str,
    title: str = "Design Agent App",
    description: str = "",
) -> str:
    """Create a complete Vite + React + Tailwind CSS project with the given components.

    Generates a production-ready, mobile-first responsive React application.
    The components parameter should be a JSON array of objects, each with 'name' and 'code' keys.

    Args:
        project_name: Directory name for the project (created under /tmp).
        components: JSON array of components. Each: {"name": "ComponentName", "code": "... tsx/jsx code ..."}.
        title: HTML page title.
        description: Short app description for meta tags.

    Returns:
        JSON with project_path and build status.
    """
    try:
        project_name = safe_project_name(project_name)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    project_path = Path(f"/tmp/design-agent-builds/{project_name}")
    if project_path.exists():
        shutil.rmtree(project_path)
    project_path.mkdir(parents=True)

    parsed_components = json.loads(components) if isinstance(components, str) else components

    _write_package_json(project_path, project_name)
    _write_vite_config(project_path, project_name)
    _write_tailwind_config(project_path)
    _write_postcss_config(project_path)
    _write_index_html(project_path, title, description)
    _write_index_css(project_path)
    _write_main_tsx(project_path)
    _write_app_tsx(project_path, parsed_components)
    _write_motion_utils(project_path)
    _write_tsconfig(project_path)
    _write_vite_env_dts(project_path)
    _write_gitignore(project_path)

    src_dir = project_path / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)
    for comp in parsed_components:
        try:
            cname = safe_component_name(comp["name"])
        except ValueError as e:
            return json.dumps({"error": str(e)})
        comp_file = src_dir / f"{cname}.tsx"
        comp_file.write_text(comp["code"])

    if NODE_MODULES_CACHE.is_dir() and _cache_version_matches():
        shutil.copytree(NODE_MODULES_CACHE, project_path / "node_modules", symlinks=True)
        if LOCK_CACHE.is_file():
            shutil.copy2(LOCK_CACHE, project_path / "package-lock.json")
    else:
        _clear_cache()
        result = subprocess.run(
            ["npm", "install", "--yes", "--fetch-retries=2", "--fetch-timeout=30000"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return json.dumps({"error": "npm install failed", "stderr": result.stderr[:500], "project_path": str(project_path)})
        _save_cache(project_path)

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=project_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return json.dumps({"error": "build failed", "stderr": result.stderr[:500], "project_path": str(project_path)})

    return json.dumps({
        "project_path": str(project_path),
        "dist_path": str(project_path / "dist"),
        "build_status": "success",
        "component_count": len(parsed_components),
    })


def _write_package_json(path: Path, name: str) -> None:
    pkg = {
        "name": name,
        "private": True,
        "version": "0.1.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
        },
        "dependencies": {
            "react": "^19.0.0",
            "react-dom": "^19.0.0",
            "motion": "^12.0.0",
            "gsap": "^3.12.0",
            "@gsap/react": "^2.1.0",
            "lucide-react": "^0.460.0",
        },
        "devDependencies": {
            "@types/react": "^19.0.0",
            "@types/react-dom": "^19.0.0",
            "@vitejs/plugin-react": "^4.3.0",
            "autoprefixer": "^10.4.20",
            "postcss": "^8.4.49",
            "tailwindcss": "^3.4.0",
            "typescript": "~5.6.0",
            "vite": "^6.0.0",
        },
    }
    (path / "package.json").write_text(json.dumps(pkg, indent=2))


def _write_vite_config(path: Path, project_name: str) -> None:
    (path / "vite.config.ts").write_text(dedent(f"""\
        import {{ defineConfig }} from 'vite'
        import react from '@vitejs/plugin-react'

        export default defineConfig({{
          plugins: [react()],
          base: '/{project_name}/',
          build: {{ outDir: 'dist' }},
        }})
    """))


def _write_tailwind_config(path: Path) -> None:
    (path / "tailwind.config.js").write_text(dedent("""\
        /** @type {import('tailwindcss').Config} */
        export default {
          content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
          theme: {
            extend: {
              animation: {
                'fade-in': 'fadeIn 0.6s ease-out forwards',
                'fade-up': 'fadeUp 0.6s ease-out forwards',
                'slide-in-left': 'slideInLeft 0.6s ease-out forwards',
                'slide-in-right': 'slideInRight 0.6s ease-out forwards',
                'scale-in': 'scaleIn 0.5s ease-out forwards',
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 4s ease-in-out infinite',
              },
              keyframes: {
                fadeIn: {
                  '0%': { opacity: '0' },
                  '100%': { opacity: '1' },
                },
                fadeUp: {
                  '0%': { opacity: '0', transform: 'translateY(20px)' },
                  '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideInLeft: {
                  '0%': { opacity: '0', transform: 'translateX(-40px)' },
                  '100%': { opacity: '1', transform: 'translateX(0)' },
                },
                slideInRight: {
                  '0%': { opacity: '0', transform: 'translateX(40px)' },
                  '100%': { opacity: '1', transform: 'translateX(0)' },
                },
                scaleIn: {
                  '0%': { opacity: '0', transform: 'scale(0.95)' },
                  '100%': { opacity: '1', transform: 'scale(1)' },
                },
                float: {
                  '0%, 100%': { transform: 'translateY(0)' },
                  '50%': { transform: 'translateY(-10px)' },
                },
              },
            },
          },
          plugins: [],
        }
    """))


def _write_postcss_config(path: Path) -> None:
    (path / "postcss.config.js").write_text(dedent("""\
        export default {
          plugins: {
            tailwindcss: {},
            autoprefixer: {},
          },
        }
    """))


def _write_index_html(path: Path, title: str, description: str) -> None:
    (path / "index.html").write_text(dedent(f"""\
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <meta name="description" content="{description}" />
            <title>{title}</title>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/main.tsx"></script>
          </body>
        </html>
    """))


def _write_index_css(path: Path) -> None:
    src = path / "src"
    src.mkdir(exist_ok=True)
    (src / "index.css").write_text(dedent("""\
        @tailwind base;
        @tailwind components;
        @tailwind utilities;

        @layer base {
          html {
            scroll-behavior: smooth;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
          }

          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }

          ::selection {
            background-color: rgb(var(--color-primary, 59 130 246) / 0.2);
          }
        }

        @layer utilities {
          .text-balance {
            text-wrap: balance;
          }

          .gpu-accelerated {
            will-change: transform;
            transform: translateZ(0);
          }
        }
    """))


def _write_main_tsx(path: Path) -> None:
    src = path / "src"
    src.mkdir(exist_ok=True)
    (src / "main.tsx").write_text(dedent("""\
        import React from 'react'
        import ReactDOM from 'react-dom/client'
        import App from './App'
        import './index.css'

        ReactDOM.createRoot(document.getElementById('root')!).render(
          <React.StrictMode>
            <App />
          </React.StrictMode>,
        )
    """))


def _write_app_tsx(path: Path, components: list[dict]) -> None:
    import_lines: list[str] = []
    jsx_names: list[str] = []
    for c in components:
        name = c["name"]
        if name == "App":
            import_lines.append(f"import {{ default as AppContent }} from './components/App'")
            jsx_names.append("AppContent")
        else:
            import_lines.append(f"import {name} from './components/{name}'")
            jsx_names.append(name)

    src = path / "src"
    src.mkdir(exist_ok=True)

    lines = import_lines.copy()
    lines.append("")
    lines.append("export default function App() {")
    lines.append("  return (")
    lines.append('    <div className="min-h-screen bg-white">')
    for name in jsx_names:
        lines.append(f"      <{name} />")
    lines.append("    </div>")
    lines.append("  )")
    lines.append("}")
    lines.append("")
    (src / "App.tsx").write_text("\n".join(lines))


def _write_motion_utils(path: Path) -> None:
    utils_dir = path / "src" / "utils"
    utils_dir.mkdir(parents=True, exist_ok=True)
    (utils_dir / "motion.tsx").write_text(dedent("""\
        import { motion, type Variants, useInView } from "motion/react"
        import { useRef, type ReactNode } from "react"

        const fadeUp: Variants = {
          hidden: { opacity: 0, y: 30 },
          visible: { opacity: 1, y: 0 },
        }

        const fadeIn: Variants = {
          hidden: { opacity: 0 },
          visible: { opacity: 1 },
        }

        const slideInLeft: Variants = {
          hidden: { opacity: 0, x: -60 },
          visible: { opacity: 1, x: 0 },
        }

        const slideInRight: Variants = {
          hidden: { opacity: 0, x: 60 },
          visible: { opacity: 1, x: 0 },
        }

        const scaleIn: Variants = {
          hidden: { opacity: 0, scale: 0.9 },
          visible: { opacity: 1, scale: 1 },
        }

        type AnimationVariant = "fadeUp" | "fadeIn" | "slideInLeft" | "slideInRight" | "scaleIn"

        const variantMap: Record<AnimationVariant, Variants> = {
          fadeUp,
          fadeIn,
          slideInLeft,
          slideInRight,
          scaleIn,
        }

        interface AnimateInProps {
          children: ReactNode
          variant?: AnimationVariant
          delay?: number
          duration?: number
          className?: string
          once?: boolean
        }

        export function AnimateIn({
          children,
          variant = "fadeUp",
          delay = 0,
          duration = 0.6,
          className,
          once = true,
        }: AnimateInProps) {
          const ref = useRef<HTMLDivElement>(null)
          const isInView = useInView(ref, { once, margin: "-80px" })

          return (
            <motion.div
              ref={ref}
              variants={variantMap[variant]}
              initial="hidden"
              animate={isInView ? "visible" : "hidden"}
              transition={{ duration, delay, ease: [0.25, 0.1, 0.25, 1] }}
              className={className}
            >
              {children}
            </motion.div>
          )
        }

        interface StaggerChildrenProps {
          children: ReactNode
          staggerDelay?: number
          className?: string
        }

        export function StaggerChildren({
          children,
          staggerDelay = 0.1,
          className,
        }: StaggerChildrenProps) {
          const ref = useRef<HTMLDivElement>(null)
          const isInView = useInView(ref, { once: true, margin: "-60px" })

          return (
            <motion.div
              ref={ref}
              initial="hidden"
              animate={isInView ? "visible" : "hidden"}
              variants={{
                visible: { transition: { staggerChildren: staggerDelay } },
              }}
              className={className}
            >
              {children}
            </motion.div>
          )
        }

        export function StaggerItem({
          children,
          className,
        }: {
          children: ReactNode
          className?: string
        }) {
          return (
            <motion.div
              variants={fadeUp}
              transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
              className={className}
            >
              {children}
            </motion.div>
          )
        }

        export { motion, type Variants }
    """))


def _write_tsconfig(path: Path) -> None:
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "isolatedModules": True,
            "moduleDetection": "force",
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": False,
            "noUnusedLocals": False,
            "noUnusedParameters": False,
            "noFallthroughCasesInSwitch": True,
            "noUncheckedSideEffectImports": True,
        },
        "include": ["src"],
    }
    (path / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))


def _write_vite_env_dts(path: Path) -> None:
    src = path / "src"
    src.mkdir(exist_ok=True)
    (src / "vite-env.d.ts").write_text('/// <reference types="vite/client" />\n')


def _write_gitignore(path: Path) -> None:
    (path / ".gitignore").write_text("node_modules/\ndist/\n*.local\n")
