// ========================================
// RAILWAY RESERVATION SYSTEM
// JavaScript
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    // Automatically hide flash messages
    const flashMessages = document.querySelectorAll(".flash");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.style.opacity = "0";

            setTimeout(function () {
                message.remove();
            }, 400);

        }, 4000);

    });


    // Confirm booking forms
    const bookingForms =
        document.querySelectorAll("form[data-confirm-booking]");

    bookingForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const confirmed = confirm(
                "Do you want to confirm this railway booking?"
            );

            if (!confirmed) {
                event.preventDefault();
            }

        });

    });


    // Confirm cancellation forms
    const cancelForms =
        document.querySelectorAll("form[data-confirm-cancel]");

    cancelForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const confirmed = confirm(
                "Are you sure you want to cancel this booking?"
            );

            if (!confirmed) {
                event.preventDefault();
            }

        });

    });

});