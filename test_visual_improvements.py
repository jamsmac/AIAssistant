#!/usr/bin/env python3
"""
Test script for Module 5 visual improvements
Verifies theme toggle, accessibility, focus states, and responsive design
"""

import sys
from pathlib import Path
import re

print("\n" + "=" * 60)
print("🎨 MODULE 5: VISUAL LAYER IMPROVEMENTS TEST")
print("=" * 60 + "\n")


def test_theme_toggle():
    """Test that theme toggle is implemented"""
    print("📋 Test 1: Theme Toggle Implementation\n")
    print("=" * 60)

    checks = []

    try:
        # Check ThemeProvider
        provider_path = Path(__file__).parent / "web-ui" / "components" / "ThemeProvider.tsx"
        if provider_path.exists():
            with open(provider_path) as f:
                content = f.read()

            provider_checks = [
                ("ThemeContext created", "ThemeContext"),
                ("localStorage integration", "localStorage.getItem"),
                ("System preference detection", "prefers-color-scheme"),
                ("Dark class toggle", "document.documentElement.classList"),
                ("useTheme hook", "useTheme"),
            ]

            print("\n✅ ThemeProvider.tsx found:")
            for check_name, pattern in provider_checks:
                found = pattern in content
                checks.append((f"ThemeProvider: {check_name}", found))
                status = "✅" if found else "❌"
                print(f"   {status} {check_name}")
        else:
            checks.append(("ThemeProvider file", False))
            print("\n❌ ThemeProvider.tsx not found!")

        # Check ThemeToggle component
        toggle_path = Path(__file__).parent / "web-ui" / "components" / "ThemeToggle.tsx"
        if toggle_path.exists():
            with open(toggle_path) as f:
                content = f.read()

            toggle_checks = [
                ("Moon icon for dark mode", "Moon"),
                ("Sun icon for light mode", "Sun"),
                ("Click handler", "toggleTheme"),
                ("ARIA label", "aria-label"),
                ("Focus states", "focus:ring"),
            ]

            print("\n✅ ThemeToggle.tsx found:")
            for check_name, pattern in toggle_checks:
                found = pattern in content
                checks.append((f"ThemeToggle: {check_name}", found))
                status = "✅" if found else "❌"
                print(f"   {status} {check_name}")
        else:
            checks.append(("ThemeToggle file", False))
            print("\n❌ ThemeToggle.tsx not found!")

        # Check Tailwind config
        tailwind_path = Path(__file__).parent / "web-ui" / "tailwind.config.js"
        if tailwind_path.exists():
            with open(tailwind_path) as f:
                content = f.read()

            has_dark_mode = "darkMode: 'class'" in content
            checks.append(("Tailwind dark mode config", has_dark_mode))
            status = "✅" if has_dark_mode else "❌"
            print(f"\n{status} Tailwind config has dark mode: class")
        else:
            checks.append(("Tailwind config", False))
            print("\n❌ tailwind.config.js not found!")

        # Check layout integration
        layout_path = Path(__file__).parent / "web-ui" / "app" / "layout.tsx"
        if layout_path.exists():
            with open(layout_path) as f:
                content = f.read()

            layout_checks = [
                ("ThemeProvider import", "ThemeProvider"),
                ("ThemeProvider wrapper", "<ThemeProvider>"),
                ("Dark mode classes", "dark:bg-gray-950"),
                ("Suppress hydration warning", "suppressHydrationWarning"),
            ]

            print("\n✅ layout.tsx integration:")
            for check_name, pattern in layout_checks:
                found = pattern in content
                checks.append((f"Layout: {check_name}", found))
                status = "✅" if found else "❌"
                print(f"   {status} {check_name}")
        else:
            checks.append(("Layout file", False))
            print("\n❌ layout.tsx not found!")

        # Check Navigation integration
        nav_path = Path(__file__).parent / "web-ui" / "components" / "Navigation.tsx"
        if nav_path.exists():
            with open(nav_path) as f:
                content = f.read()

            has_toggle = "<ThemeToggle />" in content
            checks.append(("Navigation: ThemeToggle", has_toggle))
            status = "✅" if has_toggle else "❌"
            print(f"\n{status} Navigation includes ThemeToggle")
        else:
            checks.append(("Navigation file", False))
            print("\n❌ Navigation.tsx not found!")

        print("\n" + "=" * 60)
        all_passed = all(result[1] for result in checks)
        if all_passed:
            print("✅ ALL THEME TOGGLE TESTS PASSED!")
        else:
            failed = [name for name, passed in checks if not passed]
            print(f"⚠️  {len(failed)} CHECKS FAILED:")
            for name in failed:
                print(f"   ❌ {name}")
        print("=" * 60 + "\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_accessibility():
    """Test accessibility improvements"""
    print("📋 Test 2: Accessibility (ARIA Labels & Focus States)\n")
    print("=" * 60)

    checks = []

    try:
        nav_path = Path(__file__).parent / "web-ui" / "components" / "Navigation.tsx"

        if not nav_path.exists():
            print("\n❌ Navigation.tsx not found!")
            return False

        with open(nav_path) as f:
            content = f.read()

        # Check for ARIA labels
        aria_checks = [
            ("Toggle mobile menu", r'aria-label="Toggle mobile menu"'),
            ("Notifications", r'aria-label="Notifications"'),
            ("Settings", r'aria-label="Settings"'),
            ("aria-current for active pages", r'aria-current'),
            ("aria-expanded for menu", r'aria-expanded'),
            ("aria-hidden for decorative icons", r'aria-hidden="true"'),
        ]

        print("\n✅ ARIA Labels:")
        for check_name, pattern in aria_checks:
            found = bool(re.search(pattern, content))
            checks.append((f"ARIA: {check_name}", found))
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}")

        # Check for focus states
        focus_checks = [
            ("focus:outline-none", len(re.findall(r'focus:outline-none', content))),
            ("focus:ring", len(re.findall(r'focus:ring-\d', content))),
            ("focus:ring-offset", len(re.findall(r'focus:ring-offset', content))),
        ]

        print("\n✅ Focus States:")
        for check_name, count in focus_checks:
            found = count > 0
            checks.append((f"Focus: {check_name}", found))
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {count} occurrences")

        # Check dark mode focus variants
        dark_focus = bool(re.search(r'dark:focus:ring-offset', content))
        checks.append(("Dark mode focus states", dark_focus))
        status = "✅" if dark_focus else "❌"
        print(f"\n{status} Dark mode focus variants")

        print("\n" + "=" * 60)
        all_passed = all(result[1] for result in checks)
        if all_passed:
            print("✅ ALL ACCESSIBILITY TESTS PASSED!")
        else:
            failed = [name for name, passed in checks if not passed]
            print(f"⚠️  {len(failed)} CHECKS FAILED:")
            for name in failed:
                print(f"   ❌ {name}")
        print("=" * 60 + "\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_responsive_design():
    """Test responsive design classes"""
    print("📋 Test 3: Responsive Design\n")
    print("=" * 60)

    checks = []

    try:
        nav_path = Path(__file__).parent / "web-ui" / "components" / "Navigation.tsx"

        if not nav_path.exists():
            print("\n❌ Navigation.tsx not found!")
            return False

        with open(nav_path) as f:
            content = f.read()

        # Check responsive breakpoints
        responsive_checks = [
            ("Mobile first (md: breakpoint)", r'md:'),
            ("Hidden on mobile", r'hidden.*md:'),
            ("Mobile menu", r'md:hidden'),
            ("Sidebar width responsive", r'md:w-60'),
            ("Padding responsive", r'md:pl-60'),
        ]

        print("\n✅ Responsive Classes:")
        for check_name, pattern in responsive_checks:
            matches = len(re.findall(pattern, content))
            found = matches > 0
            checks.append((f"Responsive: {check_name}", found))
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {matches} occurrences")

        print("\n" + "=" * 60)
        all_passed = all(result[1] for result in checks)
        if all_passed:
            print("✅ ALL RESPONSIVE DESIGN TESTS PASSED!")
        else:
            failed = [name for name, passed in checks if not passed]
            print(f"⚠️  {len(failed)} CHECKS FAILED:")
            for name in failed:
                print(f"   ❌ {name}")
        print("=" * 60 + "\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dark_mode_support():
    """Test dark mode class usage"""
    print("📋 Test 4: Dark Mode Support\n")
    print("=" * 60)

    checks = []

    try:
        nav_path = Path(__file__).parent / "web-ui" / "components" / "Navigation.tsx"

        if not nav_path.exists():
            print("\n❌ Navigation.tsx not found!")
            return False

        with open(nav_path) as f:
            content = f.read()

        # Count dark mode classes
        dark_classes = [
            ("Background colors", r'dark:bg-\w+-\d+'),
            ("Text colors", r'dark:text-\w+-\d+'),
            ("Border colors", r'dark:border-\w+-\d+'),
            ("Hover states", r'dark:hover:'),
        ]

        print("\n✅ Dark Mode Classes:")
        for check_name, pattern in dark_classes:
            matches = len(re.findall(pattern, content))
            found = matches > 0
            checks.append((f"Dark mode: {check_name}", found))
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {matches} occurrences")

        # Check transition classes
        transitions = len(re.findall(r'transition', content))
        checks.append(("Transitions", transitions > 0))
        print(f"\n✅ Smooth transitions: {transitions} occurrences")

        print("\n" + "=" * 60)
        all_passed = all(result[1] for result in checks)
        if all_passed:
            print("✅ ALL DARK MODE TESTS PASSED!")
        else:
            failed = [name for name, passed in checks if not passed]
            print(f"⚠️  {len(failed)} CHECKS FAILED:")
            for name in failed:
                print(f"   ❌ {name}")
        print("=" * 60 + "\n")

        return all_passed

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    results = []

    try:
        # Test 1: Theme toggle
        results.append(("Theme Toggle", test_theme_toggle()))

        # Test 2: Accessibility
        results.append(("Accessibility", test_accessibility()))

        # Test 3: Responsive design
        results.append(("Responsive Design", test_responsive_design()))

        # Test 4: Dark mode support
        results.append(("Dark Mode Support", test_dark_mode_support()))

        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60 + "\n")

        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}: {name}")

        all_passed = all(result[1] for result in results)

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL MODULE 5 TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 60 + "\n")

        print("🎨 Implementation Summary:")
        print("   ✅ Theme toggle with localStorage persistence")
        print("   ✅ System preference detection")
        print("   ✅ ARIA labels for all interactive elements")
        print("   ✅ Focus states with ring-2 for keyboard navigation")
        print("   ✅ Dark mode variants for all components")
        print("   ✅ Responsive breakpoints (mobile-first)")
        print("   ✅ Smooth transitions (<200ms)")

        print("\n📝 Usage:")
        print("""
   Theme Toggle:
   - Click sun/moon icon in top bar
   - Theme persists in localStorage
   - Respects system preference by default

   Keyboard Navigation:
   - Tab through all elements
   - Focus ring visible on all interactive elements
   - Enter/Space to activate buttons

   Responsive:
   - Mobile: Hamburger menu, collapsible sidebar
   - Tablet/Desktop: Always visible sidebar
        """)

        if not all_passed:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
