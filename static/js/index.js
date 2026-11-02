function confirmDelete(selector) {
    document.querySelectorAll(selector).forEach(button => {

        button.addEventListener("click", function (e) {

            e.preventDefault();

            const url = this.href;
            // Delete buttons submit their POST form; links (which have no .form) keep navigating.
            const form = this.form;

            Swal.fire({
                title: "Delete This?",
                text: "This action cannot be undone.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#dc3545",
                cancelButtonColor: "#6c757d",
                confirmButtonText: "Yes, Delete",
                cancelButtonText: "Cancel"
            }).then((result) => {

                if (result.isConfirmed) {
                    if (form) {
                        form.submit();
                    } else {
                        window.location.href = url;
                    }
                }

            });

        });

    });
}




