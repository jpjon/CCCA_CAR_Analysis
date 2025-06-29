// Generate colors for each year with distinct before/after colors
export function generateYearColors(years) {
    const colors = {};
    years.forEach((year, index) => {
        const hue = (index * 360 / years.length) % 360;
        // Create distinct colors for before (previous year) and after (current year)
        colors[year] = {
            before: `hsl(${hue}, 90%, 70%)`, // Brighter for "before" state
            after: `hsl(${hue}, 30%, 50%)`   // Darker/muted for "after" state
        };
    });
    return colors;
}