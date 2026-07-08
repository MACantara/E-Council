document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.show-password-button').forEach(function (button) {
        button.addEventListener('click', function () {
            const input = document.getElementById(this.getAttribute('data-target'));
            if (input) {
                input.type = input.type === 'password' ? 'text' : 'password';
            }
        });
    });
});
