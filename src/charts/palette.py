PALETTES: dict[str, list[str]] = {
    "professional": ["#2563EB", "#64748B", "#0F172A", "#3B82F6", "#94A3B8", "#1E3A5F"],
    "warm": ["#DC2626", "#EA580C", "#D97706", "#CA8A04", "#65A30D", "#16A34A"],
    "cool": ["#0891B2", "#0284C7", "#7C3AED", "#6D28D9", "#4F46E5", "#2563EB"],
    "vibrant": ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6", "#EC4899"],
}


def get_palette(name: str = "professional") -> list[str]:
    return PALETTES.get(name, PALETTES["professional"])
