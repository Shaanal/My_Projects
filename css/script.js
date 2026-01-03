// number of particles
const PARTICLE_COUNT = 90;

const container = document.querySelector('.particles');

for (let i = 0; i < PARTICLE_COUNT; i++) {
    const p = document.createElement("div");
    p.classList.add("particle");

    // random starting position
    p.style.left = Math.random() * 100 + "%";
    p.style.top = Math.random() * 100 + "%";

    // random animation timing
    p.style.animationDuration = 3 + Math.random() * 3 + "s";
    p.style.animationDelay = Math.random() * 2 + "s";

    container.appendChild(p);
}
