document.addEventListener('DOMContentLoaded', () => {
    const transitionLinks = document.querySelectorAll('.t');

    transitionLinks.forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            const href = link.getAttribute('href');

            document.querySelector('*').classList.add('transition-leave');

            setTimeout(() => {
                window.location.href = href;
            }, 500); // Match the transition duration
        });
    });
});

window.addEventListener('load', () => {
    document.querySelector('*').classList.add('transition-enter');
    setTimeout(() => {
        document.querySelector('*').classList.remove('transition-enter');
    }, 500); // Match the transition duration
});