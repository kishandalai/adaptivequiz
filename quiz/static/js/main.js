document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.display = 'none';
        }, 4000);
    });

    const navToggle = document.querySelector('.nav-toggle');
    const navigation = document.getElementById('site-navigation');
    if (navToggle && navigation) {
        navToggle.addEventListener('click', function () {
            const expanded = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', String(!expanded));
            navigation.classList.toggle('is-open', !expanded);
        });
    }
});
