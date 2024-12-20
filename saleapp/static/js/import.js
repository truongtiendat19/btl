function addRow() {
            const table = document.getElementById("importTable");
            const row = table.insertRow(-1);
            row.innerHTML = `
                <td>${table.rows.length}</td>
                <td><input type="text" name="book" class="form-control" required></td>
                <td><input type="text" name="category" class="form-control" required></td>
                <td><input type="text" name="author" class="form-control" required></td>
                <td><input type="number" name="quantity" class="form-control" min="150" max="300" required></td>
                <td><button type="button" class="btn btn-danger" onclick="removeRow(this)">-</button></td>
            `;
        }

        function removeRow(button) {
            const row = button.closest('tr');
            row.remove();
        }