import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import Sidebar from '../Sidebar'
import { ThemeProvider } from '../../../contexts/ThemeContext'

describe('Sidebar Theme Adaptation', () => {
  const renderSidebar = (theme = 'dark') => {
    // Set data-theme attribute for testing
    document.documentElement.dataset.theme = theme

    return render(
      <ThemeProvider>
        <BrowserRouter>
          <Sidebar />
        </BrowserRouter>
      </ThemeProvider>
    )
  }

  describe('Dark Theme', () => {
    it('should render with theme-appropriate background classes', () => {
      const { container } = renderSidebar('dark')
      const sidebar = container.querySelector('aside')

      expect(sidebar).toHaveClass('bg-surface/60')
      expect(sidebar).toHaveClass('backdrop-blur-xl')
    })

    it('should render logo with primary color', () => {
      renderSidebar('dark')
      const logo = screen.getByText('Obsidian Hub')

      expect(logo).toHaveClass('text-primary')
    })

    it('should render logo image with correct theme', () => {
      renderSidebar('dark')
      const logo = screen.getByAltText('Prospecta')

      expect(logo).toBeInTheDocument()
      expect(logo).toHaveAttribute('src', '/logo-branca.png')
    })

    it('should render navigation items with theme tokens', () => {
      const { container } = renderSidebar('dark')
      const navLinks = container.querySelectorAll('a')

      // Check that nav links exist
      expect(navLinks.length).toBeGreaterThan(0)

      // Verify they use theme-appropriate classes
      navLinks.forEach(link => {
        const classes = link.className
        // Should contain theme token classes for hover states
        expect(classes).toMatch(/hover:text-primary|hover:bg-surface-container-low/)
      })
    })

    it('should render border with outline-variant token', () => {
      const { container } = renderSidebar('dark')
      const sidebar = container.querySelector('aside')

      expect(sidebar).toHaveClass('border-outline-variant/15')
    })
  })

  describe('Light Theme', () => {
    it('should render with theme-appropriate background classes', () => {
      const { container } = renderSidebar('light')
      const sidebar = container.querySelector('aside')

      // Same classes, but CSS variables will be different
      expect(sidebar).toHaveClass('bg-surface/60')
      expect(sidebar).toHaveClass('backdrop-blur-xl')
    })

    it('should render logo with primary color', () => {
      renderSidebar('light')
      const logo = screen.getByText('Obsidian Hub')

      expect(logo).toHaveClass('text-primary')
    })

    it('should render logo image with correct theme', () => {
      renderSidebar('light')
      const logo = screen.getByAltText('Prospecta')

      expect(logo).toBeInTheDocument()
      expect(logo).toHaveAttribute('src', '/logo-preta.png')
    })
  })

  describe('Glassmorphism Effects', () => {
    it('should apply backdrop-blur for glassmorphism', () => {
      const { container } = renderSidebar('dark')
      const sidebar = container.querySelector('aside')

      expect(sidebar).toHaveClass('backdrop-blur-xl')
    })

    it('should have shadow effect', () => {
      const { container } = renderSidebar('dark')
      const sidebar = container.querySelector('aside')

      // Check for shadow class
      expect(sidebar.className).toContain('shadow-')
    })
  })

  describe('Navigation States', () => {
    it('should have active state classes for navigation items', () => {
      const { container } = renderSidebar('dark')
      const navLinks = container.querySelectorAll('a')

      // At least one link should be active (Dashboard at '/')
      const activeLink = Array.from(navLinks).find(link =>
        link.className.includes('text-primary') &&
        link.className.includes('bg-surface-container')
      )

      expect(activeLink).toBeTruthy()
    })

    it('should have hover state classes for navigation items', () => {
      const { container } = renderSidebar('dark')
      const navLinks = container.querySelectorAll('a')

      navLinks.forEach(link => {
        expect(link.className).toMatch(/hover:text-primary/)
        expect(link.className).toMatch(/hover:bg-surface-container-low/)
      })
    })
  })

  describe('Theme Token Usage', () => {
    it('should not contain hardcoded color values', () => {
      const { container } = renderSidebar('dark')
      const sidebar = container.querySelector('aside')

      // Check that inline styles don't contain hardcoded colors
      const inlineStyle = sidebar.getAttribute('style')
      if (inlineStyle) {
        expect(inlineStyle).not.toMatch(/#[0-9a-fA-F]{6}/)
        expect(inlineStyle).not.toMatch(/rgb\(\d+,\s*\d+,\s*\d+\)/)
      }
    })

    it('should use semantic color classes', () => {
      const { container } = renderSidebar('dark')
      const html = container.innerHTML

      // Should contain theme token classes
      expect(html).toMatch(/text-primary|text-on-surface|text-on-surface-variant/)
      expect(html).toMatch(/bg-surface|bg-surface-container/)
    })
  })
})
