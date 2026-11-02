import React, { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import helpText from '../help/help_text.json'

// Space kept between an open panel and the edge of the window, in pixels.
const EDGE_GAP = 8

// A round "?" button that opens a short help panel. The text comes from
// src/help/help_text.json, looked up by helpKey. Place it after a label, never
// inside one, so a click cannot toggle a checkbox or open a file dialog.
export const HelpButton = ({ helpKey }) => {
  const [open, setOpen] = useState(false)
  const [shift, setShift] = useState(0)
  const wrapperRef = useRef(null)
  const buttonRef = useRef(null)
  const panelRef = useRef(null)
  const panelId = useId()

  // Close on a click outside this button and its panel, or on Escape.
  useEffect(() => {
    if (!open) return undefined
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    const handleKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false)
        buttonRef.current?.focus()
      }
    }
    document.addEventListener('click', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('click', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  // Keep the open panel inside the window, for buttons near the right edge.
  useLayoutEffect(() => {
    if (!open || !panelRef.current) {
      setShift(0)
      return
    }
    const rect = panelRef.current.getBoundingClientRect()
    const overflow = rect.right - (window.innerWidth - EDGE_GAP)
    setShift(overflow > 0 ? Math.min(overflow, rect.left - EDGE_GAP) : 0)
  }, [open])

  if (!Object.hasOwn(helpText.entries, helpKey)) {
    throw new Error(`Unknown help key: ${helpKey}`)
  }
  const { title, text } = helpText.entries[helpKey]

  return (
    <span ref={wrapperRef} className="relative inline-flex ml-1.5 flex-shrink-0">
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen(!open)}
        aria-label={`Help for ${title}`}
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        aria-describedby={open ? panelId : undefined}
        className="inline-flex items-center justify-center w-5 h-5 p-0 rounded-full border-2 border-blue-600 text-blue-600 bg-transparent text-xs font-bold leading-none cursor-pointer hover:bg-blue-600 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-1 dark:border-blue-400 dark:text-blue-400 dark:hover:bg-blue-400 dark:hover:text-gray-900 dark:ring-offset-gray-800"
      >
        ?
      </button>
      {open && (
        <span
          ref={panelRef}
          id={panelId}
          role="tooltip"
          style={shift ? { transform: `translateX(-${shift}px)` } : undefined}
          className="absolute left-0 top-full mt-2 z-10 block w-72 max-w-[calc(100vw-2rem)] p-3 text-left text-sm font-normal whitespace-normal text-gray-700 bg-white border border-gray-200 rounded-lg shadow-lg dark:text-gray-200 dark:bg-gray-800 dark:border-gray-600"
        >
          <span className="block font-semibold text-gray-900 dark:text-white">{title}</span>
          <span className="block mt-1">{text}</span>
        </span>
      )}
    </span>
  )
}
