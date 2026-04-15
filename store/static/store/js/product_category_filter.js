document.addEventListener("DOMContentLoaded", function () {
    const parentSelect = document.getElementById("id_parent_category");
    const categorySelect = document.getElementById("id_category");

    if (!parentSelect || !categorySelect) return;

    // Disable category initially
    categorySelect.disabled = true;
    categorySelect.style.backgroundColor = "#f0f0f0";


    parentSelect.addEventListener("change", function () {
        const parentId = this.value;

        // Clear previous options
        categorySelect.innerHTML = '<option value="">Select Product</option>';

        if (!parentId) {
            categorySelect.disabled = true;
            return;
        }

        fetch(`/ajax/load-subcategories/?parent_id=${parentId}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(item => {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.text = item.name;
                    categorySelect.appendChild(option);
                });

                // Enable category after loading
                categorySelect.disabled = false;
                categorySelect.style.backgroundColor = "";

            })
            .catch(error => {
                console.error("Error loading subcategories:", error);
                categorySelect.disabled = true;
            });
    });
});
