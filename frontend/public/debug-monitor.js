// Site Debug Monitor - Inject this script into your website
(function () {
  "use strict";

  // Configuration
  const CONFIG = {
    VERSION: "0.1.9.1",
    PARENT_ORIGIN: "*", // Change this to your parent site origin for security
    Z_INDEX: 10000,
  };

  // State management
  const state = {
    isActive: false,
    interactionMode: "select", // 'select' | 'preview'
    selectedElement: null, // Single element selection (primary clicked element)
    selectedGroup: [], // Group of elements with same x-id (for dynamic content)
    hoverGroup: [], // Group of elements being hovered (for dynamic multi-element preview)
    hoverBadge: null, // Current hover badge element
    selectedBadge: null, // Current selected badge element
    selectedBadges: [], // Array of badges for multi-element selection
    hoverTarget: null, // Target element for hover badge (for repositioning)
    repositionRAF: null, // RequestAnimationFrame ID for badge repositioning
    // Inline editing state
    inlineEditElement: null, // Element currently being inline edited
    inlineEditOriginalText: "", // Original text before inline edit started
  };

  // Badge Manager - handles dynamic badge positioning with viewport collision detection
  class BadgeManager {
    constructor() {
      this.GAP = 8; // Consistent gap between element and badge
      this.VIEWPORT_PADDING = 8; // Minimum distance from viewport edges
      this.removalTimeouts = new Map(); // Track pending badge removals for cleanup
    }

    /**
     * Creates a new badge element with the given label and type
     * @param {string} label - The text to display in the badge
     * @param {string} type - Badge type: 'hover', 'dynamic', or 'selected'
     * @returns {HTMLElement} The created badge element
     */
    createBadge(label, type = "hover") {
      const badge = document.createElement("div");
      badge.className = `debug-badge ${type}`;
      badge.textContent = label;
      badge.style.opacity = "0";

      // Add accessibility attributes
      badge.setAttribute("role", "tooltip");
      badge.setAttribute("aria-live", "polite");
      badge.id = `debug-badge-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;

      document.body.appendChild(badge);
      return badge;
    }

    /**
     * Calculates the best position for a badge relative to its target element
     * Uses fallback positioning strategy: top Ã¢â€ â€™ bottom Ã¢â€ â€™ right Ã¢â€ â€™ left
     * @param {HTMLElement} element - The target element
     * @param {HTMLElement} badge - The badge element to position
     * @returns {{top: number, left: number, side: string}} Position coordinates and side
     */
    calculatePosition(element, badge) {
      const elementRect = element.getBoundingClientRect();
      const badgeRect = badge.getBoundingClientRect();

      // Define all possible positions with their fit checks
      const positions = [
        {
          side: "top",
          calc: () => ({
            top: elementRect.top - badgeRect.height - this.GAP,
            left: elementRect.left - 4.5, // Align with outline outer edge (3px offset + 1.5px stroke)
          }),
          fits: (pos) => pos.top >= this.VIEWPORT_PADDING,
        },
        {
          side: "bottom",
          calc: () => ({
            top: elementRect.bottom + this.GAP,
            left: elementRect.left - 4.5, // Align with outline outer edge (3px offset + 1.5px stroke)
          }),
          fits: (pos) =>
            pos.top + badgeRect.height <=
            window.innerHeight - this.VIEWPORT_PADDING,
        },
        {
          side: "left",
          calc: () => ({
            top: elementRect.top,
            left: elementRect.left - badgeRect.width - this.GAP,
          }),
          fits: (pos) => pos.left >= this.VIEWPORT_PADDING,
        },
        {
          side: "right",
          calc: () => ({
            top: elementRect.top,
            left: elementRect.right + this.GAP,
          }),
          fits: (pos) =>
            pos.left + badgeRect.width <=
            window.innerWidth - this.VIEWPORT_PADDING,
        },
      ];

      // Try each position in order until one fits
      for (const position of positions) {
        const pos = position.calc();

        // Adjust horizontal position to prevent left/right edge clipping
        if (position.side === "top" || position.side === "bottom") {
          // Check if badge extends beyond right edge
          if (
            pos.left + badgeRect.width >
            window.innerWidth - this.VIEWPORT_PADDING
          ) {
            pos.left =
              window.innerWidth - badgeRect.width - this.VIEWPORT_PADDING;
          }
          // Check if badge extends beyond left edge
          if (pos.left < this.VIEWPORT_PADDING) {
            pos.left = this.VIEWPORT_PADDING;
          }
        }

        // Adjust vertical position for left/right positions
        if (position.side === "left" || position.side === "right") {
          // Check if badge extends beyond bottom edge
          if (
            pos.top + badgeRect.height >
            window.innerHeight - this.VIEWPORT_PADDING
          ) {
            pos.top =
              window.innerHeight - badgeRect.height - this.VIEWPORT_PADDING;
          }
          // Check if badge extends beyond top edge
          if (pos.top < this.VIEWPORT_PADDING) {
            pos.top = this.VIEWPORT_PADDING;
          }
        }

        if (position.fits(pos)) {
          return { ...pos, side: position.side };
        }
      }

      // Fallback: constrain to viewport (should rarely happen)
      const fallback = positions[0].calc();
      return {
        top: Math.max(
          this.VIEWPORT_PADDING,
          Math.min(
            fallback.top,
            window.innerHeight - badgeRect.height - this.VIEWPORT_PADDING,
          ),
        ),
        left: Math.max(
          this.VIEWPORT_PADDING,
          Math.min(
            fallback.left,
            window.innerWidth - badgeRect.width - this.VIEWPORT_PADDING,
          ),
        ),
        side: "constrained",
      };
    }

    /**
     * Positions a badge relative to its target element
     * @param {HTMLElement} element - The target element
     * @param {HTMLElement} badge - The badge element to position
     * @param {boolean} fadeIn - Whether to fade in the badge (default: true)
     */
    positionBadge(element, badge, fadeIn = true) {
      const position = this.calculatePosition(element, badge);
      badge.style.top = `${position.top}px`;
      badge.style.left = `${position.left}px`;
      badge.dataset.side = position.side;

      // Fade in the badge (only on initial creation, not during reposition)
      if (fadeIn) {
        requestAnimationFrame(() => {
          badge.style.opacity = "1";
        });
      }
    }

    /**
     * Shows a hover badge for an element
     * @param {HTMLElement} element - The target element
     * @param {string} label - The badge label
     * @param {boolean} isDynamic - Whether the element is dynamic
     * @returns {HTMLElement} The created badge element
     */
    showHoverBadge(element, label, isDynamic = false) {
      const type = isDynamic ? "dynamic" : "hover";
      const badge = this.createBadge(label, type);
      this.positionBadge(element, badge);
      return badge;
    }

    /**
     * Shows a selected badge for an element
     * @param {HTMLElement} element - The target element
     * @param {string} label - The badge label
     * @param {boolean} isDynamic - Whether this is a dynamic element (orange badge)
     * @returns {HTMLElement} The created badge element
     */
    showSelectedBadge(element, label, isDynamic = false) {
      const badgeType = isDynamic ? "selected-dynamic" : "selected";
      const badge = this.createBadge(label, badgeType);
      this.positionBadge(element, badge);
      return badge;
    }

    /**
     * Removes a badge element from the DOM
     * @param {HTMLElement} badge - The badge to remove
     */
    removeBadge(badge) {
      if (!badge) return;

      // Cancel existing removal timeout if badge is already being removed
      if (this.removalTimeouts.has(badge)) {
        clearTimeout(this.removalTimeouts.get(badge));
        this.removalTimeouts.delete(badge);
      }

      if (badge.parentElement) {
        badge.style.opacity = "0";
        const timeoutId = setTimeout(() => {
          if (badge.parentElement) {
            badge.parentElement.removeChild(badge);
          }
          this.removalTimeouts.delete(badge);
        }, 150); // Match CSS transition duration

        this.removalTimeouts.set(badge, timeoutId);
      }
    }

    /**
     * Clean up all pending badge removals (called on deactivate)
     */
    cleanup() {
      // Clear all pending removal timeouts
      this.removalTimeouts.forEach((timeoutId) => clearTimeout(timeoutId));
      this.removalTimeouts.clear();

      // Remove all badges immediately
      document.querySelectorAll(".debug-badge").forEach((badge) => {
        if (badge.parentElement) {
          badge.parentElement.removeChild(badge);
        }
      });
    }

    /**
     * Updates the position of a badge (for scroll/resize events)
     * @param {HTMLElement} element - The target element
     * @param {HTMLElement} badge - The badge to reposition
     */
    updateBadgePosition(element, badge) {
      if (badge && element) {
        this.positionBadge(element, badge, false); // Don't fade in during reposition
      }
    }
  }

  // Create global badge manager instance
  const badgeManager = new BadgeManager();

  // Utility functions
  function rgbToHex(rgb) {
    // Handle rgb(r, g, b) and rgba(r, g, b, a) formats
    const match = rgb.match(/rgba?\(([^)]+)\)/);
    if (!match) return null;

    const values = match[1].split(",").map((v) => parseFloat(v.trim()));
    if (values.length < 3) return null;

    const r = Math.round(values[0]);
    const g = Math.round(values[1]);
    const b = Math.round(values[2]);

    return (
      "#" +
      [r, g, b]
        .map((x) => {
          const hex = x.toString(16);
          return hex.length === 1 ? "0" + hex : hex;
        })
        .join("")
        .toUpperCase()
    );
  }

  function extractOpacity(color) {
    // Extract alpha from rgba() or return 1 for rgb()
    const match = color.match(/rgba?\(([^)]+)\)/);
    if (!match) return 1;

    const values = match[1].split(",").map((v) => parseFloat(v.trim()));
    return values.length === 4 ? values[3] : 1;
  }

  function parseColor(colorValue) {
    if (
      !colorValue ||
      colorValue === "transparent" ||
      colorValue === "rgba(0, 0, 0, 0)"
    ) {
      return { hex: null, opacity: 0, hasColor: false };
    }

    const hex = rgbToHex(colorValue);
    const opacity = extractOpacity(colorValue);

    return {
      hex: hex,
      opacity: Math.round(opacity * 100), // Convert to percentage
      hasColor: true,
    };
  }

  function sendMessageToParent(data) {
    if (window.parent && window.parent !== window) {
      try {
        window.parent.postMessage(
          {
            type: "SITE_DEBUG",
            source: window.location.href,
            timestamp: Date.now(),
            ...data,
          },
          CONFIG.PARENT_ORIGIN,
        );
      } catch (error) {
        // Silently fail
      }
    }
  }

  function getDirectTextContent(element) {
    // Extract only direct text nodes, not from child elements
    let text = "";
    for (let node of element.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {
        text += node.textContent;
      }
    }
    return text.trim();
  }

  // Check if element is dynamic (not directly editable)
  // Dynamic means either:
  // 1. Element has x-dynamic="true" (has expression content like {variable})
  // 2. Element is multi-instance (rendered via .map(), multiple DOM elements with same x-id)
  function isElementDynamic(element) {
    // Check the element's own x-dynamic attribute (has expressions)
    if (element.getAttribute("x-dynamic") === "true") {
      return true;
    }

    // Check if this element is multi-instance (from .map() rendering)
    // If there are multiple DOM elements with the same x-id, it's multi-instance
    const elementId = element.getAttribute("x-id");
    if (elementId) {
      const instances = document.querySelectorAll(`[x-id="${elementId}"]`);
      if (instances.length > 1) {
        return true;
      }
    }

    return false;
  }

  /**
   * Classifies an element based on its source tracking attributes
   * @param {HTMLElement} element - The element to classify
   * @returns {Object} Classification info: { isDynamic, isEditable, editType, sourceInfo }
   */
  function classifyElement(element) {
    const result = {
      isDynamic: false,
      isEditable: true,
      editType: "textContent", // Default: direct text editing
      sourceInfo: null,
    };

    // Check basic dynamic status
    const xDynamic = element.getAttribute("x-dynamic");
    const elementId = element.getAttribute("x-id");

    // Check multi-instance (from .map())
    let instanceCount = 1;
    if (elementId) {
      const instances = document.querySelectorAll(`[x-id="${elementId}"]`);
      instanceCount = instances.length;
    }

    result.isDynamic = xDynamic === "true" || instanceCount > 1;

    // If not dynamic, it's a simple static element - editable
    if (!result.isDynamic) {
      return result;
    }

    // For dynamic elements, check source type for editability
    const sourceType = element.getAttribute("x-source-type");
    const sourceEditable = element.getAttribute("x-source-editable");

    // Collect source info
    result.sourceInfo = {
      type: sourceType || null,
      varName: element.getAttribute("x-source-var") || null,
      file: element.getAttribute("x-source-file") || null,
      fileAbs: element.getAttribute("x-source-file-abs") || null,
      line: element.getAttribute("x-source-line") || null,
      path: element.getAttribute("x-source-path") || null,
      editable: sourceEditable === "true",
      // Array context
      arrayVar: element.getAttribute("x-array-var") || null,
      arrayFile: element.getAttribute("x-array-file") || null,
      arrayLine: element.getAttribute("x-array-line") || null,
      itemParam: element.getAttribute("x-array-item-param") || null,
    };

    // Determine editability based on source type
    // Editable: static-local, static-imported (with editable flag)
    // Not editable: prop, state, computed, external, unknown
    if (sourceEditable === "true") {
      result.isEditable = true;
      result.editType = "variableEdit";
    } else if (sourceType === "static-local" || sourceType === "static-imported") {
      // Check if explicitly marked as editable
      result.isEditable = sourceEditable === "true";
      result.editType = result.isEditable ? "variableEdit" : "readonly";
    } else if (sourceType === "prop" || sourceType === "state" ||
               sourceType === "computed" || sourceType === "external") {
      result.isEditable = false;
      result.editType = "readonly";
    } else {
      // Unknown type - default to not editable for safety
      result.isEditable = false;
      result.editType = "readonly";
    }

    // Check if source is shared with other elements (different x-id)
    // If shared, editing this element would affect others - mark as non-editable
    if (result.isEditable && result.sourceInfo) {
      const sharedCheck = checkSharedSource(element);
      if (sharedCheck.isShared) {
        result.isEditable = false;
        result.editType = "sharedSource";
        result.sourceInfo.isSharedSource = true;
        result.sourceInfo.sharedCount = sharedCheck.sharedCount;
      }
    }

    return result;
  }

  /**
   * Checks if an element's source data is shared with other elements
   * (elements with different x-id that use the same underlying data)
   *
   * Detects two sharing patterns:
   * 1. Direct source: same variable used in multiple places (e.g., {data.title} twice)
   * 2. Array iteration: same array data accessed via different .map() calls
   *
   * @param {HTMLElement} element - The element to check
   * @returns {{ isShared: boolean, sharedCount: number, sharedElements: HTMLElement[] }}
   */
  function checkSharedSource(element) {
    const sourceVar = element.getAttribute("x-source-var");
    const sourceFileAbs = element.getAttribute("x-source-file-abs");
    const sourcePath = element.getAttribute("x-source-path");
    const arrayVar = element.getAttribute("x-array-var");
    const arrayFile = element.getAttribute("x-array-file");
    const elementId = element.getAttribute("x-id");

    // If no source tracking, can't determine sharing
    if (!sourceVar) {
      return { isShared: false, sharedCount: 0, sharedElements: [] };
    }

    let sharedElements = [];

    // Strategy 1: Check for elements with same direct source (same var, file, path)
    // This catches: const data = {title: "Hi"}; <h1>{data.title}</h1> <p>{data.title}</p>
    if (sourceFileAbs) {
      let directSelector = `[x-source-var="${sourceVar}"][x-source-file-abs="${CSS.escape(sourceFileAbs)}"]`;
      if (sourcePath) {
        directSelector += `[x-source-path="${sourcePath}"]`;
      }
      const directMatches = document.querySelectorAll(directSelector);
      directMatches.forEach(el => {
        const otherId = el.getAttribute("x-id");
        if (otherId !== elementId && el !== element && !sharedElements.includes(el)) {
          sharedElements.push(el);
        }
      });
    }

    // Strategy 2: Check for elements using same array data (via .map())
    // This catches: deliveryOptions.map(o => <h3>{o.name}</h3>) and deliveryOptions.map(o => <span>{o.name}</span>)
    // Even across different files, if they iterate the same array and access same path
    if (arrayVar && arrayFile && sourcePath) {
      let arraySelector = `[x-array-var="${arrayVar}"][x-array-file="${CSS.escape(arrayFile)}"][x-source-path="${sourcePath}"]`;
      const arrayMatches = document.querySelectorAll(arraySelector);
      arrayMatches.forEach(el => {
        const otherId = el.getAttribute("x-id");
        if (otherId !== elementId && el !== element && !sharedElements.includes(el)) {
          sharedElements.push(el);
        }
      });
    }

    return {
      isShared: sharedElements.length > 0,
      sharedCount: sharedElements.length,
      sharedElements
    };
  }

  /**
   * Gets the array index for a .map() rendered element by finding its position
   * among siblings with the same x-id
   * @param {HTMLElement} element - The element to find the index for
   * @returns {number|null} The array index or null if not in an array
   */
  function getArrayIndexFromDOM(element) {
    const elementId = element.getAttribute("x-id");
    if (!elementId) return null;

    const instances = document.querySelectorAll(`[x-id="${elementId}"]`);
    if (instances.length <= 1) return null;

    // Find the index of this element
    const instanceArray = Array.from(instances);
    const index = instanceArray.indexOf(element);

    return index >= 0 ? index : null;
  }

  function getElementInfo(element) {
    const rect = element.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(element);

    // Extract color information
    const textColor = parseColor(computedStyle.color);
    const backgroundColor = parseColor(computedStyle.backgroundColor);
    const borderColor = parseColor(computedStyle.borderColor);

    // Get only direct text content (not from child elements)
    const directText = getDirectTextContent(element);
    const hasDirectTextContent = directText.length > 0;

    const childElementCount = element.children ? element.children.length : 0;

    return {
      tagName: element.tagName.toLowerCase(),
      id: element.id || null,
      className: element.className || null,
      textContent: directText || null,
      hasDirectTextContent: hasDirectTextContent,
      hasChildElements: childElementCount > 0,
      childElementCount: childElementCount,
      attributes: Array.from(element.attributes).reduce((acc, attr) => {
        acc[attr.name] = attr.value;
        return acc;
      }, {}),
      rect: {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
      },
      computedStyles: {
        color: textColor,
        backgroundColor: backgroundColor,
        borderColor: borderColor,
        fontSize: computedStyle.fontSize,
        fontWeight: computedStyle.fontWeight,
        fontFamily: computedStyle.fontFamily,
        textAlign: computedStyle.textAlign,
        lineHeight: computedStyle.lineHeight,
        letterSpacing: computedStyle.letterSpacing,
        textDecoration: computedStyle.textDecoration,
        fontStyle: computedStyle.fontStyle,
        display: computedStyle.display,
        position: computedStyle.position,
        marginTop: computedStyle.marginTop,
        marginRight: computedStyle.marginRight,
        marginBottom: computedStyle.marginBottom,
        marginLeft: computedStyle.marginLeft,
        paddingTop: computedStyle.paddingTop,
        paddingRight: computedStyle.paddingRight,
        paddingBottom: computedStyle.paddingBottom,
        paddingLeft: computedStyle.paddingLeft,
      },
    };
  }

  // Visual highlighting system
  function createStyles() {
    const style = document.createElement("style");
    style.id = "debug-monitor-styles";
    style.textContent = `
            /* Hover state - dotted lines (editable elements) */
            [data-debug-hover]:not([data-debug-selected]):not([data-debug-dynamic]) {
                outline: 2px dotted #5288CC !important;
                outline-offset: 2px !important;
            }

            /* Hover state for dynamic elements (not editable) - orange/warning color */
            [data-debug-hover][data-debug-dynamic]:not([data-debug-selected]) {
                outline: 2px dotted #FF8C42 !important;
                outline-offset: 2px !important;
            }

            /* Selected state - solid lines */
            [data-debug-selected]:not([data-debug-dynamic]) {
                outline: 1.5px solid #2764EB !important;
                outline-offset: 3px !important;
                box-shadow: 0 0 0 1px rgba(39, 100, 235, 0.3), inset 0 0 0 999px rgba(39, 100, 235, 0.05) !important;
            }

            /* Selected state for dynamic elements - orange solid */
            [data-debug-selected][data-debug-dynamic] {
                outline: 1.5px solid #FF8C42 !important;
                outline-offset: 3px !important;
                box-shadow: 0 0 0 1px rgba(255, 140, 66, 0.3), inset 0 0 0 999px rgba(255, 140, 66, 0.05) !important;
            }

            /* Badge element styles (created dynamically in JS) */
            .debug-badge {
                position: fixed;
                z-index: ${CONFIG.Z_INDEX};
                pointer-events: none;
                padding: 4px 6px 4px 22px;
                border-radius: 6px;
                font-size: 11px;
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-weight: bold;
                white-space: nowrap;
                background-repeat: no-repeat;
                background-position: 4px center;
                background-size: 14px 14px;
                transition: top 0.15s ease-out, left 0.15s ease-out, opacity 0.15s ease-out;
            }

            /* Badge variants */
            .debug-badge.hover {
                background-color: #DBEAFE;
                border: 1px solid #B5CBF6;
                color: #1E4ED8;
                background-image: url('data:image/svg+xml;utf8,<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M5.93934 1.06066L7 0L8.06066 1.06066L12.9393 5.93934L14 7L12.9393 8.06066L8.06066 12.9393L7 14L5.93934 12.9393L1.06066 8.06066L0 7L1.06066 5.93934L5.93934 1.06066ZM2.12132 7L7 11.8787L11.8787 7L7 2.12132L2.12132 7Z" fill="%231E4ED8"/></svg>');
            }

            .debug-badge.dynamic {
                background-color: #FFF5E6;
                border: 1px solid #FFCC99;
                color: #CC5500;
                background-image: url('data:image/svg+xml;utf8,<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 0L8.5 5.5L14 7L8.5 8.5L7 14L5.5 8.5L0 7L5.5 5.5L7 0Z" fill="%23CC5500"/></svg>');
            }

            .debug-badge.selected {
                background-color: #1E4ED8;
                border: 1px solid #1E4ED8;
                color: white;
                background-image: url('data:image/svg+xml;utf8,<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M5.93934 1.06066L7 0L8.06066 1.06066L12.9393 5.93934L14 7L12.9393 8.06066L8.06066 12.9393L7 14L5.93934 12.9393L1.06066 8.06066L0 7L1.06066 5.93934L5.93934 1.06066ZM2.12132 7L7 11.8787L11.8787 7L7 2.12132L2.12132 7Z" fill="white"/></svg>');
            }

            .debug-badge.selected-dynamic {
                background-color: #FF8C42;
                border: 1px solid #FF8C42;
                color: white;
                background-image: url('data:image/svg+xml;utf8,<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 0L8.5 5.5L14 7L8.5 8.5L7 14L5.5 8.5L0 7L5.5 5.5L7 0Z" fill="white"/></svg>');
            }



            /* Ensure debug badges are always visible */
            .debug-badge {
                pointer-events: none !important;
                display: block !important;
            }
        `;
    document.head.appendChild(style);
  }

  const INTERACTION_BLOCK_EVENTS = [
    "pointerdown",
    "pointerup",
    "touchstart",
    "touchend",
    "mousedown",
    "mouseup",
    "contextmenu",
  ];

  // Prevent interactive behavior when we're in select mode
  function blockInteractiveEvent(event) {
    if (!state.isActive) return;
    if (state.interactionMode !== "select") return;

    // Allow modifier-assisted interactions (e.g., holding meta for native browser behavior)
    if (event.metaKey || event.ctrlKey || event.altKey) {
      return;
    }

    // Allow all interactions on the element being inline edited (cursor, selection, etc.)
    if (state.inlineEditElement) {
      const target = event.target;
      if (target === state.inlineEditElement || state.inlineEditElement.contains(target)) {
        return;
      }
    }

    event.preventDefault();
    event.stopPropagation();
  }

  // Event handlers - simplified for click-only selection

  function handleClick(event) {
    if (!state.isActive) return;

    // PREVIEW MODE: Allow normal interaction, don't intercept
    if (state.interactionMode === "preview") {
      return;
    }

    const element = event.target;

    // If clicking on the element being inline edited, allow normal click (cursor positioning)
    if (state.inlineEditElement && (element === state.inlineEditElement || state.inlineEditElement.contains(element))) {
      return;
    }

    // If clicking on a different element while inline editing, save and disable inline edit first
    if (state.inlineEditElement) {
      disableInlineEdit(true); // Save changes before selecting new element
    }

    // SELECT MODE: Intercept for element selection
    event.preventDefault();
    event.stopPropagation();

    // Exclude SVG elements from selection
    if (element.tagName && element.tagName.toLowerCase() === "svg") {
      return;
    }

    // Exclude Toast and Sonner components from selection
    const componentName = element.getAttribute("x-component");
    if (
      componentName &&
      (componentName.startsWith("Toast") ||
        componentName === "Toaster" ||
        componentName === "Sonner")
    ) {
      return;
    }

    // Check if element is inside a Toast/Sonner component
    const toastParent = element.closest(
      '[x-component^="Toast"], [x-component="Toaster"], [x-component="Sonner"]'
    );
    if (toastParent) {
      return;
    }

    const elementInfo = getElementInfo(element);

    // Ensure element has x-id for tracking (assign temp ID if missing)
    // This is needed for pendingChanges queue and DOM targeting
    if (!elementInfo.attributes["x-id"]) {
      const generatedId = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
      element.setAttribute("x-id", generatedId);
      elementInfo.attributes["x-id"] = generatedId;
    }
    // Validate that element has required metadata attributes
    // Elements without metadata are not part of React component tree and can't be edited
    const hasRequiredMetadata =
      elementInfo.attributes["x-file-name"] &&
      elementInfo.attributes["x-line-number"] &&
      elementInfo.attributes["x-component"];

    if (!hasRequiredMetadata) {
      return;
    }

    // Classify the element to determine editability and source type
    const classification = classifyElement(element);
    const isDynamic = isElementDynamic(element);

    // Get array index if this is a .map() rendered element
    const arrayIndex = getArrayIndexFromDOM(element);

    // Clear previous selection
    if (state.selectedElement && state.selectedElement !== element) {
      // Clear previous single element selection
      state.selectedElement.removeAttribute("data-debug-selected");
      if (state.selectedBadge) {
        badgeManager.removeBadge(state.selectedBadge);
        state.selectedBadge = null;
      }

      // Clear previous group selection
      state.selectedGroup.forEach((el) => {
        el.removeAttribute("data-debug-selected");
      });
      state.selectedBadges.forEach((badge) => {
        badgeManager.removeBadge(badge);
      });
      state.selectedGroup = [];
      state.selectedBadges = [];
    }

    // Select new element (or deselect if clicking the same element)
    if (state.selectedElement === element) {
      // Deselect
      state.selectedElement = null;
      element.removeAttribute("data-debug-selected");

      // Remove badge(s)
      if (state.selectedBadge) {
        badgeManager.removeBadge(state.selectedBadge);
        state.selectedBadge = null;
      }
      state.selectedGroup.forEach((el) => {
        el.removeAttribute("data-debug-selected");
        el.removeAttribute("data-debug-dynamic");
      });
      state.selectedBadges.forEach((badge) => {
        badgeManager.removeBadge(badge);
      });
      state.selectedGroup = [];
      state.selectedBadges = [];

      sendMessageToParent({
        action: "ELEMENT_DESELECTED",
      });
    } else {
      // Select new element
      state.selectedElement = element;

      // For dynamic elements, find ALL elements with the same x-id
      // But if they're editable, treat them as editable (not dynamic)
      const showAsDynamic = isDynamic && !classification.isEditable;

      if (isDynamic && elementInfo.attributes["x-id"]) {
        const elementId = elementInfo.attributes["x-id"];
        const allElements = document.querySelectorAll(`[x-id="${elementId}"]`);
        state.selectedGroup = Array.from(allElements).filter(Boolean);

        // Mark all elements as selected
        // Only add dynamic flag if NOT editable
        state.selectedGroup.forEach((el) => {
          el.setAttribute("data-debug-selected", "true");
          if (showAsDynamic) {
            el.setAttribute("data-debug-dynamic", "true");
          }
        });

        // Create badge - show "Dynamic" only if not editable
        const label = showAsDynamic
          ? `${element.tagName.toLowerCase()} (Dynamic)`
          : element.tagName.toLowerCase();
        const badge = badgeManager.showSelectedBadge(element, label, showAsDynamic);
        state.selectedBadges = [badge]; // Single badge in array
      } else {
        // Single element selection (non-dynamic)
        element.setAttribute("data-debug-selected", "true");
        const label = element.tagName.toLowerCase();
        state.selectedBadge = badgeManager.showSelectedBadge(
          element,
          label,
          false,
        );
      }

      // Get element position for widget placement
      // Use viewport-relative coordinates (no scroll offset)
      // Parent will add iframe position to convert to parent viewport coordinates
      const rect = element.getBoundingClientRect();

      sendMessageToParent({
        action: "ELEMENT_SELECTED",
        element: elementInfo,
        isDynamic: isDynamic,
        isEditable: classification.isEditable,
        editType: classification.editType,
        sourceInfo: classification.sourceInfo,
        arrayIndex: arrayIndex,
        elementCount: isDynamic ? state.selectedGroup.length : 1,
        isMultiElement: isDynamic && state.selectedGroup.length > 1,
        position: {
          x: rect.left,
          y: rect.bottom, // Position below the element
          width: rect.width,
          height: rect.height,
          elementRect: {
            top: rect.top,
            left: rect.left,
            bottom: rect.bottom,
            right: rect.right,
          },
        },
      });
    }
  }

  // Message handler for parent communication
  function handleParentMessage(event) {
    // For security, you should set CONFIG.PARENT_ORIGIN to your actual parent origin
    if (event.origin !== CONFIG.PARENT_ORIGIN && CONFIG.PARENT_ORIGIN !== "*")
      return;

    const { type, action, data } = event.data;

    if (type !== "DEBUG_COMMAND") return;

    switch (action) {
      case "ACTIVATE":
        activateDebugMode();
        break;
      case "DEACTIVATE":
        deactivateDebugMode();
        break;
      case "CLEAR_SELECTION":
        clearSelection();
        break;
      case "APPLY_CHANGES":
        applyElementChanges(event.data.data);
        break;
      case "SET_INTERACTION_MODE":
        setInteractionMode(data.mode);
        break;
      case "ENABLE_INLINE_EDIT":
        enableInlineEdit(data);
        break;
      case "DISABLE_INLINE_EDIT":
        disableInlineEdit(data?.save !== false);
        break;
    }
  }

  // Hover handlers
  function handleMouseEnter(event) {
    if (!state.isActive) return;

    // PREVIEW MODE: No hover effects
    if (state.interactionMode === "preview") {
      return;
    }

    // SELECT MODE: Show hover effects
    const element = event.target;

    // Validate element is a proper DOM Element node
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return;

    // Don't add hover effect to already selected element
    if (element.hasAttribute("data-debug-selected")) return;

    // Exclude SVG elements from hover highlighting
    if (element.tagName && element.tagName.toLowerCase() === "svg") {
      return;
    }

    // Exclude Toast and Sonner components from hover
    const componentName = element.getAttribute("x-component");
    if (
      componentName &&
      (componentName.startsWith("Toast") ||
        componentName === "Toaster" ||
        componentName === "Sonner")
    ) {
      return;
    }

    // Check if element has required metadata attributes
    // Elements without metadata are not part of React component tree
    const hasRequiredMetadata =
      element.hasAttribute("x-file-name") &&
      element.hasAttribute("x-line-number") &&
      element.hasAttribute("x-component");

    if (!hasRequiredMetadata) {
      return;
    }

    // Check if element is dynamic (checks element AND ancestors)
    const isDynamic = isElementDynamic(element);

    // Classify the element to check editability
    const classification = classifyElement(element);

    // Show as dynamic only if dynamic AND not editable
    const showAsDynamic = isDynamic && !classification.isEditable;

    // For dynamic elements, highlight ALL instances with same x-id
    if (isDynamic) {
      const elementId =
        element.getAttribute("x-id") ||
        element.closest("[x-id]")?.getAttribute("x-id");

      if (elementId) {
        // Find all elements with same x-id
        const allElements = document.querySelectorAll(`[x-id="${elementId}"]`);
        state.hoverGroup = Array.from(allElements).filter(Boolean);

        // Check if ANY element in the group is selected
        const anySelected = state.hoverGroup.some((el) =>
          el.hasAttribute("data-debug-selected"),
        );

        if (anySelected) {
          // Don't show hover effects if group is already selected
          state.hoverGroup = [];
          return;
        }

        // Mark all elements with hover
        // Only add dynamic flag if NOT editable
        state.hoverGroup.forEach((el) => {
          el.setAttribute("data-debug-hover", "true");
          if (showAsDynamic) {
            el.setAttribute("data-debug-dynamic", "true");
          }
        });
      } else {
        // Fallback: single element if no x-id found
        element.setAttribute("data-debug-hover", "true");
        if (showAsDynamic) {
          element.setAttribute("data-debug-dynamic", "true");
        }
      }
    } else {
      // Single element hover (non-dynamic)
      element.setAttribute("data-debug-hover", "true");
    }

    // Create and show badge - show "Dynamic" only if not editable
    const label = showAsDynamic
      ? `${element.tagName.toLowerCase()} (Dynamic)`
      : element.tagName.toLowerCase();

    // Remove previous hover badge if exists
    if (state.hoverBadge) {
      badgeManager.removeBadge(state.hoverBadge);
    }

    // Store target element reference for repositioning
    state.hoverTarget = element;
    state.hoverBadge = badgeManager.showHoverBadge(element, label, showAsDynamic);
  }

  function handleMouseLeave(event) {
    if (!state.isActive) return;

    // PREVIEW MODE: No hover effects to remove
    if (state.interactionMode === "preview") {
      return;
    }

    // SELECT MODE: Remove hover effects
    const element = event.target;

    // Validate element is a proper DOM Element node
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return;

    // Clear single element or all elements in hoverGroup
    if (state.hoverGroup.length > 0) {
      // Multi-element hover - clear all
      state.hoverGroup.forEach((el) => {
        el.removeAttribute("data-debug-hover");
        // Only remove data-debug-dynamic if element is not selected
        if (!el.hasAttribute("data-debug-selected")) {
          el.removeAttribute("data-debug-dynamic");
        }
      });
      state.hoverGroup = [];
    } else {
      // Single element hover - clear just this one
      element.removeAttribute("data-debug-hover");
      // Only remove data-debug-dynamic if element is not selected
      if (!element.hasAttribute("data-debug-selected")) {
        element.removeAttribute("data-debug-dynamic");
      }
    }

    // Remove hover badge and clear target reference
    if (state.hoverBadge) {
      badgeManager.removeBadge(state.hoverBadge);
      state.hoverBadge = null;
      state.hoverTarget = null;
    }
  }

  // Badge repositioning on scroll/resize
  let repositionTimeout;
  function handleBadgeReposition() {
    // Immediately hide badges and disable transitions to prevent visual lag during scroll
    if (state.hoverBadge) {
      state.hoverBadge.style.opacity = "0";
      state.hoverBadge.style.transition = "none";
    }
    if (state.selectedBadge) {
      state.selectedBadge.style.opacity = "0";
      state.selectedBadge.style.transition = "none";
    }
    if (state.selectedBadges.length > 0) {
      state.selectedBadges.forEach((badge) => {
        badge.style.opacity = "0";
        badge.style.transition = "none";
      });
    }

    clearTimeout(repositionTimeout);
    repositionTimeout = setTimeout(() => {
      // Cancel pending RAF to prevent stacking
      if (state.repositionRAF) {
        cancelAnimationFrame(state.repositionRAF);
      }

      state.repositionRAF = requestAnimationFrame(() => {
        // Reposition hover badge using stored target reference
        if (state.hoverBadge && state.hoverTarget) {
          badgeManager.updateBadgePosition(state.hoverTarget, state.hoverBadge);
          // Force reflow to commit position changes before re-enabling transitions
          void state.hoverBadge.offsetHeight;
          // Re-enable transitions and show badge
          state.hoverBadge.style.transition = "";
          state.hoverBadge.style.opacity = "1";
        }

        // Reposition selected badge (single element)
        if (state.selectedBadge && state.selectedElement) {
          badgeManager.updateBadgePosition(
            state.selectedElement,
            state.selectedBadge,
          );
          // Force reflow to commit position changes before re-enabling transitions
          void state.selectedBadge.offsetHeight;
          // Re-enable transitions and show badge
          state.selectedBadge.style.transition = "";
          state.selectedBadge.style.opacity = "1";
        }

        // Reposition badge for multi-element selection (only first element has badge)
        if (state.selectedBadges.length > 0 && state.selectedGroup.length > 0) {
          badgeManager.updateBadgePosition(
            state.selectedGroup[0],
            state.selectedBadges[0],
          );
          // Force reflow to commit position changes before re-enabling transitions
          void state.selectedBadges[0].offsetHeight;
          // Re-enable transitions and show badge
          state.selectedBadges[0].style.transition = "";
          state.selectedBadges[0].style.opacity = "1";
        }

        state.repositionRAF = null;
      });
    }, 50); // 50ms debounce for smooth performance
  }

  // Debug mode controls
  function activateDebugMode() {
    state.isActive = true;
    // Set cursor based on current mode
    document.body.style.cursor =
      state.interactionMode === "select" ? "crosshair" : "default";

    // Add class to body for select mode to disable hover components
    if (state.interactionMode === "select") {
      document.body.classList.add("debug-select-mode");
    }

    // Add event listeners
    document.addEventListener("click", handleClick, true);
    document.addEventListener("mouseover", handleMouseEnter, true);
    document.addEventListener("mouseout", handleMouseLeave, true);

    INTERACTION_BLOCK_EVENTS.forEach((eventName) => {
      document.addEventListener(eventName, blockInteractiveEvent, true);
    });

    // Add scroll and resize listeners for badge repositioning
    window.addEventListener("scroll", handleBadgeReposition, { passive: true });
    window.addEventListener("resize", handleBadgeReposition, { passive: true });

    sendMessageToParent({
      action: "DEBUG_MODE_ACTIVATED",
      url: window.location.href,
    });
  }

  function deactivateDebugMode() {
    state.isActive = false;
    document.body.style.cursor = "";
    document.body.classList.remove("debug-select-mode");

    // Remove event listeners
    document.removeEventListener("click", handleClick, true);
    document.removeEventListener("mouseover", handleMouseEnter, true);
    document.removeEventListener("mouseout", handleMouseLeave, true);
    INTERACTION_BLOCK_EVENTS.forEach((eventName) => {
      document.removeEventListener(eventName, blockInteractiveEvent, true);
    });
    window.removeEventListener("scroll", handleBadgeReposition);
    window.removeEventListener("resize", handleBadgeReposition);

    // Clear pending timers and RAF
    clearTimeout(repositionTimeout);
    repositionTimeout = null;

    if (state.repositionRAF) {
      cancelAnimationFrame(state.repositionRAF);
      state.repositionRAF = null;
    }

    // Clear selection
    clearSelection();

    // Clean up all pending badge removals
    badgeManager.cleanup();

    sendMessageToParent({
      action: "DEBUG_MODE_DEACTIVATED",
    });
  }

  function clearSelection() {
    // Disable inline editing if active
    if (state.inlineEditElement) {
      disableInlineEdit(true); // Save before clearing
    }

    if (state.selectedElement) {
      state.selectedElement.removeAttribute("data-debug-selected");
      state.selectedElement = null;
    }

    // Remove selected badge (single element)
    if (state.selectedBadge) {
      badgeManager.removeBadge(state.selectedBadge);
      state.selectedBadge = null;
    }

    // Clear all elements in multi-element selection
    state.selectedGroup.forEach((el) => {
      el.removeAttribute("data-debug-selected");
      el.removeAttribute("data-debug-dynamic");
    });
    state.selectedGroup = [];

    // Remove all badges in multi-element selection
    state.selectedBadges.forEach((badge) => {
      badgeManager.removeBadge(badge);
    });
    state.selectedBadges = [];

    // Remove hover badge
    if (state.hoverBadge) {
      badgeManager.removeBadge(state.hoverBadge);
      state.hoverBadge = null;
    }

    // Clear all hover effects
    const hoveredElements = document.querySelectorAll("[data-debug-hover]");
    hoveredElements.forEach((el) => {
      el.removeAttribute("data-debug-hover");
      el.removeAttribute("data-debug-dynamic");
    });

    sendMessageToParent({
      action: "ELEMENT_DESELECTED",
    });
  }

  function setInteractionMode(mode) {
    state.interactionMode = mode;

    // Update cursor based on mode
    if (state.isActive) {
      document.body.style.cursor = mode === "select" ? "crosshair" : "default";

      // Add/remove class for select mode
      if (mode === "select") {
        document.body.classList.add("debug-select-mode");
      } else {
        document.body.classList.remove("debug-select-mode");
      }
    }

    sendMessageToParent({
      action: "INTERACTION_MODE_CHANGED",
      mode: mode,
    });
  }

  // Apply changes to the selected element or by element ID
  function applyElementChanges(changes) {
    let targetElements = [];      // Elements for content changes (specific element)
    let appearanceTargets = [];   // Elements for appearance changes (all siblings for array elements)

    // If elementId is provided, find element(s) by x-id attribute
    if (changes.elementId) {
      // Check if this is a multi-element update (dynamic content)
      if (changes.isMultiElement) {
        const elements = document.querySelectorAll(
          `[x-id="${changes.elementId}"]`,
        );
        const allElements = Array.from(elements).filter(Boolean);

        // For appearance/layout changes (className, attributes), always target ALL siblings
        // These changes modify the JSX template which renders all elements
        appearanceTargets = allElements;

        // If arrayIndex is provided, only target that specific element for content changes
        if (changes.arrayIndex !== undefined && changes.arrayIndex !== null) {
          const targetElement = allElements[changes.arrayIndex];
          if (targetElement) {
            targetElements = [targetElement];
          } else {
            sendMessageToParent({
              action: "CHANGES_ERROR",
              error: `Element at arrayIndex ${changes.arrayIndex} not found`,
              elementId: changes.elementId,
              arrayIndex: changes.arrayIndex,
            });
            return;
          }
        } else {
          // No arrayIndex: update all elements (legacy behavior)
          targetElements = allElements;
        }
      } else {
        const element = document.querySelector(`[x-id="${changes.elementId}"]`);
        if (!element) {
          sendMessageToParent({
            action: "CHANGES_ERROR",
            error: `Element not found: x-id="${changes.elementId}"`,
            elementId: changes.elementId,
          });
          return;
        }

        targetElements = [element];
        appearanceTargets = [element];
      }
    } else {
      // Fallback to selected element for backwards compatibility
      if (!state.selectedElement) {
        sendMessageToParent({
          action: "CHANGES_ERROR",
          error: "No element selected and no elementId provided",
        });
        return;
      }
      targetElements = [state.selectedElement];
      appearanceTargets = [state.selectedElement];
    }

    if (targetElements.length === 0) {
      sendMessageToParent({
        action: "CHANGES_ERROR",
        error: "No elements found",
        elementId: changes.elementId,
      });
      return;
    }

    let applied = [];

    try {
      // Apply text content changes to targetElements (specific element only)
      // Text content is data-specific (e.g., item.title) - only update the clicked element
      targetElements.forEach((element, index) => {
        // Apply text content changes ONLY if element has direct text content
        // Allow for single elements OR when arrayIndex is provided (targeting specific element)
        const isSingleTargetUpdate = !changes.isMultiElement ||
          (changes.arrayIndex !== undefined && changes.arrayIndex !== null);
        if (changes.textContent !== undefined && isSingleTargetUpdate) {
          const hasDirectText =
            element.getAttribute("x-direct-text") === "true";
          const hasChildren = element.children && element.children.length > 0;

          if (hasDirectText || !hasChildren) {
            // Safe to apply textContent: element has direct text OR no children
            element.textContent = changes.textContent;
            if (index === 0) applied.push("textContent");
          } else {
            // Mixed content: update an existing text node (or create one) without touching child elements
            const textNodes = Array.from(element.childNodes).filter(
              (node) => node.nodeType === Node.TEXT_NODE,
            );
            const firstTextNode =
              textNodes.find(
                (node) =>
                  node.textContent && node.textContent.trim().length > 0,
              ) || textNodes[0];

            if (firstTextNode) {
              // Preserve original leading/trailing whitespace if the update omits it
              const originalText = firstTextNode.textContent || "";
              const originalLeading = (originalText.match(/^\s+/) || [""])[0];
              const originalTrailing = (originalText.match(/\s+$/) || [""])[0];
              const updateLeading = (changes.textContent.match(/^\s+/) || [
                "",
              ])[0];
              const updateTrailing = (changes.textContent.match(/\s+$/) || [
                "",
              ])[0];
              const coreText = changes.textContent.trim();
              firstTextNode.textContent = `${updateLeading || originalLeading}${coreText}${updateTrailing || originalTrailing}`;
            } else {
              const textNode = document.createTextNode(changes.textContent);
              element.insertBefore(textNode, element.firstChild || null);
            }

            if (index === 0) {
              applied.push("textContent");
            }
          }
        }

        // Apply ID changes (only for single element - multiple elements can't share same ID)
        if (changes.id !== undefined && !changes.isMultiElement) {
          if (changes.id) {
            element.id = changes.id;
          } else {
            element.removeAttribute("id");
          }
          if (index === 0) applied.push("id");
        }
      });

      // Apply appearance/layout changes to ALL siblings (appearanceTargets)
      // These changes modify the JSX template which renders all array elements identically
      appearanceTargets.forEach((element, index) => {
        // Apply class changes to all siblings
        if (changes.className !== undefined) {
          element.className = changes.className;
          if (index === 0) applied.push("className");
        }

        // Apply custom attributes to all siblings (except x-* metadata attributes)
        if (changes.attributes && typeof changes.attributes === "object") {
          Object.entries(changes.attributes).forEach(([key, value]) => {
            // Skip x-* metadata attributes - those should not be modified
            if (key.startsWith("x-")) return;
            if (value) {
              element.setAttribute(key, value);
            } else {
              element.removeAttribute(key);
            }
          });
          if (index === 0) applied.push("attributes");
        }
      });
    } catch (error) {
      sendMessageToParent({
        action: "CHANGES_ERROR",
        error: error.message,
        elementId: changes.elementId,
      });
    }
  }

  // Inline editing event handlers
  function handleInlineInput(event) {
    const element = event.target;
    sendMessageToParent({
      action: "INLINE_EDIT_CHANGE",
      elementId: element.getAttribute("x-id"),
      textContent: element.textContent,
    });
  }

  function handleInlineKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      disableInlineEdit(true); // Save
    } else if (event.key === "Escape") {
      event.preventDefault();
      disableInlineEdit(false); // Cancel/revert
    }
  }

  function handleInlineBlur(event) {
    // Small delay to check if focus moved to another element we care about
    setTimeout(() => {
      if (state.inlineEditElement && document.activeElement !== state.inlineEditElement) {
        disableInlineEdit(true); // Save on blur
      }
    }, 100);
  }

  // Enable inline editing on the selected element
  function enableInlineEdit(data) {
    const elementId = data?.elementId;
    const arrayIndex = data?.arrayIndex;
    let element = null;

    if (elementId) {
      // For array elements, we need to get the specific instance by index
      const allInstances = document.querySelectorAll(`[x-id="${elementId}"]`);
      if (allInstances.length > 1 && arrayIndex !== undefined && arrayIndex !== null) {
        element = allInstances[arrayIndex];
      } else {
        element = allInstances[0] || null;
      }
    } else if (state.selectedElement) {
      element = state.selectedElement;
    }

    if (!element) {
      sendMessageToParent({
        action: "INLINE_EDIT_ERROR",
        error: "No element found for inline editing",
        elementId: elementId,
      });
      return;
    }

    // Check if element can be inline edited
    const classification = classifyElement(element);
    const hasDirectText = getDirectTextContent(element).length > 0;

    // Reject if:
    // 1. No direct text content to edit, OR
    // 2. Element is dynamic AND not marked as editable
    if (!hasDirectText || (classification.isDynamic && !classification.isEditable)) {
      sendMessageToParent({
        action: "INLINE_EDIT_ERROR",
        error: classification.isDynamic
          ? "Dynamic element is not editable (source cannot be traced)"
          : "Element has no direct text content",
        elementId: elementId,
        isDynamic: classification.isDynamic,
        isEditable: classification.isEditable,
      });
      return;
    }

    // Store original text for cancel/revert
    state.inlineEditOriginalText = element.textContent;
    state.inlineEditElement = element;

    // Enable contentEditable
    element.contentEditable = "true";
    element.style.outline = "none"; // Remove default contentEditable outline
    element.style.cursor = "text";

    // Focus and place cursor at the end (blinking cursor, no selection)
    element.focus();
    const range = document.createRange();
    range.selectNodeContents(element);
    range.collapse(false); // Collapse to end
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    // Add event listeners
    element.addEventListener("input", handleInlineInput);
    element.addEventListener("keydown", handleInlineKeydown);
    element.addEventListener("blur", handleInlineBlur);

    // Notify parent
    sendMessageToParent({
      action: "INLINE_EDIT_START",
      elementId: element.getAttribute("x-id"),
      textContent: element.textContent,
    });
  }

  // Disable inline editing
  function disableInlineEdit(save = true) {
    const element = state.inlineEditElement;
    if (!element) return;

    // Remove event listeners
    element.removeEventListener("input", handleInlineInput);
    element.removeEventListener("keydown", handleInlineKeydown);
    element.removeEventListener("blur", handleInlineBlur);

    // Disable contentEditable
    element.contentEditable = "false";
    element.style.cursor = "";

    const finalText = element.textContent;
    const elementId = element.getAttribute("x-id");

    // Revert if not saving
    if (!save) {
      element.textContent = state.inlineEditOriginalText;
    }

    // Clear state
    state.inlineEditElement = null;
    const originalText = state.inlineEditOriginalText;
    state.inlineEditOriginalText = "";

    // Notify parent
    sendMessageToParent({
      action: "INLINE_EDIT_END",
      elementId: elementId,
      textContent: save ? finalText : originalText,
      originalText: originalText,
      saved: save,
    });
  }

  // Initialize
  function init() {
    // Only run if we're in an iframe
    if (window.parent === window) {
      return;
    }

    createStyles();

    // Set up communication
    window.addEventListener("message", handleParentMessage);
  }

  // Auto-initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose controls globally for manual testing
  window.siteDebugMonitor = {
    activate: activateDebugMode,
    deactivate: deactivateDebugMode,
    clearSelection: clearSelection,
    getState: () => ({ ...state }),
  };
})();
