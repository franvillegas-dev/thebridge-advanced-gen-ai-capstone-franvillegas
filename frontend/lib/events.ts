export type RefreshTarget = "tasks" | "calendar" | "dashboard"

const listeners = new Map<RefreshTarget, Set<() => void>>()

export function onRefresh(target: RefreshTarget, callback: () => void): () => void {
  if (!listeners.has(target)) {
    listeners.set(target, new Set())
  }
  listeners.get(target)!.add(callback)
  return () => {
    listeners.get(target)?.delete(callback)
  }
}

export function emitRefresh(target: RefreshTarget): void {
  listeners.get(target)?.forEach((callback) => callback())
}
