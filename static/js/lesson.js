
document.addEventListener("DOMContentLoaded", function () {

    const lessonType = document.getElementById("id_lesson_type");

    const pdfField = document.getElementById("pdf-field");
    const urlField = document.getElementById("url-field");

    function showField() {

        // Hide both first
        pdfField.style.display = "none";
        urlField.style.display = "none";

        // Show based on lesson type
        if (lessonType.value === "pdf") {
            pdfField.style.display = "block";
        }
        else if (lessonType.value === "video") {
            urlField.style.display = "block";
        }
        else if (lessonType.value === "reading") {
            document.getElementById("content-field").style.display = "block";
        }
    }

    // When page loads
    showField();

    // When user changes lesson type
    lessonType.addEventListener("change", showField);

});

document.addEventListener("DOMContentLoaded", function () {

    const input = document.getElementById("id_thumbnail");
    const preview = document.getElementById("thumbnailPreview");

    input.addEventListener("change", function () {

        const file = this.files[0];

        if (file) {
            preview.src = URL.createObjectURL(file);
            preview.style.display = "block";
        }
    });

});
