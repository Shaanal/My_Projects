// script.js
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header');
    const numberOfParticles = 100; // Adjust the number of particles

    for (let i = 1; i < numberOfParticles; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.animationDelay = `${Math.random() * 3}s`;
        header.appendChild(particle);
    }
});
