// Generate colors for each year with distinct before/after colors
export function generateYearColors(years) {
    const colors = {};
    years.forEach((year, index) => {
        const hue = (index * 360 / years.length) % 360;
        // Create distinct colors for before (previous year) and after (current year)
        colors[year] = {
            before: `hsl(${hue}, 80%, 60%)`, // Brighter for "before" state
            after: `hsl(${hue}, 40%, 60%)`   // Darker/muted for "after" state
        };
    });
    return colors;
}