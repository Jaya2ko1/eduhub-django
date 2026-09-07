
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

 document.addEventListener('DOMContentLoaded', function () {
    const courseField = document.getElementById('id_course')
    const orderNumberField = document.getElementById('id_order_number')
  
    console.log('Course field:', courseField)
    console.log('Order field:', orderNumberField)
  
    if (courseField && orderNumberField) {
      courseField.addEventListener('change', function () {
        const courseId = this.value
  
        console.log('Selected course:', courseId)
  
        if (!courseId) {
          orderNumberField.value = ''
          return
        }
  
        fetch(`/lesson/next-order-number/?course_id=${courseId}`)
          .then((response) => response.json())
          .then((data) => {
            console.log('Response:', data)
  
            orderNumberField.value = data.order_number
          })
          .catch((error) => {
            console.error('Error:', error)
          })
      })
  
      // Handle the already-selected course
      if (courseField.value) {
        courseField.dispatchEvent(new Event('change'))
      }
    }
  })


