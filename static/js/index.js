function confirmDelete(selector) {
    document.querySelectorAll(selector).forEach(button => {

        button.addEventListener("click", function (e) {

            e.preventDefault();

            const url = this.href;

            Swal.fire({
                title: "Delete Category?",
                text: "This action cannot be undone.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#dc3545",
                cancelButtonColor: "#6c757d",
                confirmButtonText: "Yes, Delete",
                cancelButtonText: "Cancel"
            }).then((result) => {

                if (result.isConfirmed) {
                    window.location.href = url;
                }

            });

        });

    });
}