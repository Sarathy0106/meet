export type MediaKind = 'microphone' | 'camera' | 'screenshare'
export type PermissionState = 'prompt' | 'granted' | 'denied' | 'unsupported'

export interface ParsedMediaError {
  kind: MediaKind
  code: string
  title: string
  message: string
  actionableStep: string
  isBlockedByBrowser: boolean
  isDeviceNotFound: boolean
  isDeviceBusy: boolean
}

/**
 * Parses any error thrown during getUserMedia or LiveKit device operations
 * into a structured, user-friendly diagnostic object.
 */
export function parseMediaError(kind: MediaKind, error: any): ParsedMediaError {
  const errorName = error?.name || error?.code || ''
  const errorMessage = error?.message || String(error || '')

  const kindLabel = kind === 'microphone' ? 'Microphone' : kind === 'camera' ? 'Camera' : 'Screen Share'

  if (
    errorName === 'NotAllowedError' ||
    errorName === 'PermissionDeniedError' ||
    errorName === 'SecurityError' ||
    errorMessage.toLowerCase().includes('permission denied') ||
    errorMessage.toLowerCase().includes('not allowed')
  ) {
    if (kind === 'screenshare') {
      return {
        kind,
        code: 'SCREENSHARE_CANCELLED',
        title: 'Screen sharing cancelled',
        message: 'You cancelled screen sharing or your system denied permission.',
        actionableStep: 'If your system blocked sharing, check System Settings > Privacy & Security > Screen Recording.',
        isBlockedByBrowser: true,
        isDeviceNotFound: false,
        isDeviceBusy: false,
      }
    }

    return {
      kind,
      code: 'PERMISSION_DENIED',
      title: `${kindLabel} access blocked`,
      message: `${kindLabel} access was blocked by your browser or rejected.`,
      actionableStep: `Click the lock (🔒) or site settings icon in your browser address bar to allow ${kindLabel.toLowerCase()} access, then try again.`,
      isBlockedByBrowser: true,
      isDeviceNotFound: false,
      isDeviceBusy: false,
    }
  }

  if (
    errorName === 'NotFoundError' ||
    errorName === 'DevicesNotFoundError' ||
    errorMessage.toLowerCase().includes('device not found')
  ) {
    return {
      kind,
      code: 'DEVICE_NOT_FOUND',
      title: `No ${kindLabel.toLowerCase()} found`,
      message: `We couldn't detect any connected ${kindLabel.toLowerCase()} on your device.`,
      actionableStep: `Please connect a ${kindLabel.toLowerCase()} or check your cable connection.`,
      isBlockedByBrowser: false,
      isDeviceNotFound: true,
      isDeviceBusy: false,
    }
  }

  if (
    errorName === 'NotReadableError' ||
    errorName === 'TrackStartError' ||
    errorMessage.toLowerCase().includes('in use') ||
    errorMessage.toLowerCase().includes('busy')
  ) {
    return {
      kind,
      code: 'DEVICE_BUSY',
      title: `${kindLabel} is in use`,
      message: `Your ${kindLabel.toLowerCase()} might be currently in use by another application (Zoom, Teams, FaceTime, etc.).`,
      actionableStep: 'Please close other apps using the device and try again.',
      isBlockedByBrowser: false,
      isDeviceNotFound: false,
      isDeviceBusy: true,
    }
  }

  if (errorName === 'OverconstrainedError' || errorName === 'ConstraintNotSatisfiedError') {
    return {
      kind,
      code: 'OVERCONSTRAINED',
      title: `${kindLabel} constraint error`,
      message: `The requested settings for your ${kindLabel.toLowerCase()} are not supported by the hardware.`,
      actionableStep: 'Try switching to a different device in Settings.',
      isBlockedByBrowser: false,
      isDeviceNotFound: false,
      isDeviceBusy: false,
    }
  }

  return {
    kind,
    code: 'UNKNOWN_ERROR',
    title: `${kindLabel} error`,
    message: errorMessage || `An unexpected error occurred while accessing your ${kindLabel.toLowerCase()}.`,
    actionableStep: 'Please check your browser permissions and device settings.',
    isBlockedByBrowser: false,
    isDeviceNotFound: false,
    isDeviceBusy: false,
  }
}

/**
 * Queries the Permissions API for microphone or camera if supported by the browser.
 */
export async function queryPermissionState(name: 'microphone' | 'camera'): Promise<PermissionState> {
  try {
    if (!navigator.permissions || !navigator.permissions.query) {
      return 'unsupported'
    }
    const status = await navigator.permissions.query({ name: name as PermissionName })
    return (status.state as PermissionState) || 'prompt'
  } catch {
    // Some browsers throw TypeError for certain descriptor names
    return 'unsupported'
  }
}

/**
 * Listens for live browser permission changes (e.g. user toggles Allow/Block in address bar).
 * Returns an unlisten cleanup function.
 */
export function listenToPermissionChanges(
  name: 'microphone' | 'camera',
  onChange: (state: PermissionState) => void
): () => void {
  let isCleanedUp = false
  let permissionStatus: PermissionStatus | null = null

  const cleanup = () => {
    isCleanedUp = true
    if (permissionStatus) {
      permissionStatus.onchange = null
    }
  }

  if (typeof navigator !== 'undefined' && navigator.permissions && navigator.permissions.query) {
    navigator.permissions
      .query({ name: name as PermissionName })
      .then((status) => {
        if (isCleanedUp) return
        permissionStatus = status
        status.onchange = () => {
          onChange((status.state as PermissionState) || 'prompt')
        }
      })
      .catch(() => {
        // Permissions query not supported for this descriptor
      })
  }

  return cleanup
}
