// document.addEventListener("DOMContentLoaded", function () {

//     const parentField = document.getElementById("id_parent_category");
//     const categoryField = document.getElementById("id_category");

//     if (!parentField || !categoryField) return;

//     function loadCategories(parentId, selectedId = null) {

//         categoryField.disabled = false;

//         fetch("/ajax/load-subcategories/?parent_id=" + parentId)
//         .then(response => response.json())
//         .then(data => {

//             categoryField.innerHTML = '<option value="">---------</option>';

//             data.forEach(item => {

//                 let option = document.createElement("option");
//                 option.value = item.id;
//                 option.textContent = item.name;

//                 if (selectedId && selectedId == item.id) {
//                     option.selected = true;
//                 }

//                 categoryField.appendChild(option);

//             });

//         });

//     }

//     // On change
//     parentField.addEventListener("change", function () {

//         if (this.value) {
//             loadCategories(this.value);
//         }

//     });

//     // On edit page: preserve existing selected category
//     if (parentField.value) {
//         loadCategories(parentField.value, categoryField.value);
//     }

// });