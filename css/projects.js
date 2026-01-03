const filters = document.querySelectorAll('.filter');
const cards = document.querySelectorAll('.project-card');

filters.forEach(btn => {
    btn.addEventListener('click', () => {
        
        filters.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const type = btn.dataset.filter;

        cards.forEach(card => {
            if (type === "all" || card.dataset.type === type) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    });
});
