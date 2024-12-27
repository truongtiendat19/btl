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
document.addEventListener("DOMContentLoaded", async function () {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        document.getElementById("invoice-date-display").textContent = formattedDate;

        const bookDetails = document.getElementById("book-details");
        const addBookRowBtn = document.getElementById("add-book-row");
        const totalAmountField = document.getElementById("total-amount");
        const cancelInvoiceBtn = document.getElementById("cancel-invoice");

        const fetchBooks = async () => {
            try {
                const response = await fetch('/api/books');
                if (!response.ok) throw new Error("Lỗi khi tải danh sách sách.");
                return await response.json();
            } catch (error) {
                console.error(error);
                return [];
            }
        };

        const books = await fetchBooks();

        const calculateTotalAmount = () => {
            let total = 0;
            Array.from(bookDetails.rows).forEach(row => {
                const totalField = row.querySelector('.total');
                total += parseFloat(totalField.value || 0);
            });
            totalAmountField.textContent = total.toLocaleString('vi-VN', { style: 'currency', currency: 'VND' });
        };

        const addBookRow = () => {
            const rowCount = bookDetails.rows.length + 1;
            const row = bookDetails.insertRow();

            row.innerHTML = `
                <td>${rowCount}</td>
                <td>
                    <select class="form-select book-select">
                        ${books.map(book => `<option value="${book.id}" data-category="${book.category}" data-price="${book.price}">${book.name}</option>`).join('')}
                    </select>
                </td>
                <td><input type="text" class="form-control category" readonly></td>
                <td><input type="number" class="form-control quantity" min="1" value="1"></td>
                <td><input type="text" class="form-control price" readonly></td>
                <td><input type="text" class="form-control total" readonly></td>
                <td><button type="button" class="remove-book-row">-</button></td>
            `;

            const bookSelect = row.querySelector('.book-select');
            const categoryField = row.querySelector('.category');
            const priceField = row.querySelector('.price');
            const totalField = row.querySelector('.total');
            const quantityField = row.querySelector('.quantity');

            bookSelect.addEventListener('change', function () {
                const selectedOption = this.options[this.selectedIndex];
                categoryField.value = selectedOption.getAttribute('data-category');
                priceField.value = selectedOption.getAttribute('data-price');
                totalField.value = (quantityField.value * selectedOption.getAttribute('data-price')).toFixed(2);
                calculateTotalAmount();
            });

            quantityField.addEventListener('input', function () {
                const price = parseFloat(priceField.value);
                totalField.value = (this.value * price).toFixed(2);
                calculateTotalAmount();
            });

            row.querySelector(".remove-book-row").addEventListener("click", function () {
                row.remove();
                updateRowNumbers();
                calculateTotalAmount();
            });

            bookSelect.dispatchEvent(new Event('change'));
        };

        const updateRowNumbers = () => {
            Array.from(bookDetails.rows).forEach((row, index) => {
                row.cells[0].innerText = index + 1;
            });
        };

        cancelInvoiceBtn.addEventListener("click", function () {
            if (confirm("Bạn có chắc chắn muốn hủy hóa đơn không?")) {
                bookDetails.innerHTML = "";
                totalAmountField.textContent = "0 VNĐ";
            }
        });

        addBookRowBtn.addEventListener("click", addBookRow);
    });