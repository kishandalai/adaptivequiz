document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('answerForm');
    const timeInput = document.getElementById('timeTaken');
    if (!form || !timeInput) return;

    const startedAt = Date.now();
    form.addEventListener('submit', function () {
        const elapsedSeconds = Math.round((Date.now() - startedAt) / 1000);
        timeInput.value = elapsedSeconds;
    });
});
