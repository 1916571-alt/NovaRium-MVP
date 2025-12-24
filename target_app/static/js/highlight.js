document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const targetId = params.get('highlight');
    if (targetId) {
        // Wait slightly for any dynamic rendering
        setTimeout(() => {
            const el = document.getElementById(targetId);
            if (el) {
                // Apply Highlight Style
                el.style.border = "4px solid #ef4444";
                el.style.boxShadow = "0 0 20px rgba(239, 68, 68, 0.6)";
                el.style.transition = "all 0.5s ease-in-out";
                el.style.position = "relative";
                el.style.zIndex = "50";

                // Add a label badge
                const badge = document.createElement("div");
                badge.textContent = "실험 대상 (Target)";
                badge.style.position = "absolute";
                badge.style.top = "-12px";
                badge.style.right = "10px";
                badge.style.backgroundColor = "#ef4444";
                badge.style.color = "white";
                badge.style.fontSize = "12px";
                badge.style.fontWeight = "bold";
                badge.style.padding = "4px 8px";
                badge.style.borderRadius = "12px";
                badge.style.zIndex = "51";
                badge.style.boxShadow = "0 2px 5px rgba(0,0,0,0.2)";
                el.appendChild(badge);

                // Scroll to view
                el.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }, 100);
    }
});
