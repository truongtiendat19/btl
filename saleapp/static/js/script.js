function updateCartUI(data) {
    let counters = document.getElementsByClassName("cart-counter");
    for (let c of counters)
        c.innerText = data.total_quantity;

    let amounts = document.getElementsByClassName("cart-amount");
    for (let c of amounts)
        c.innerText = data.total_amount.toLocaleString();
}

function addToCart(id, name, price) {
    fetch('/api/carts', {
        method: "POST",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {

        updateCartUI(data);
    })
}

function updateCart(productId, obj) {
    fetch(`/api/carts/${productId}`, {
        method: "put",
        body: JSON.stringify({
            "quantity": obj.value
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        updateCartUI(data);
    })
}

function deleteCart(productId) {
    if (confirm("Bạn chắc chắn xóa không?") === true) {
        fetch(`/api/carts/${productId}`, {
            method: "delete"
        }).then(res => res.json()).then(data => {
            updateCartUI(data);

            document.getElementById(`cart${productId}`).style.display = "none";
        });
    }
}

function pay() {
    if (confirm("Bạn chắc chắn thanh toán không?") === true) {
        fetch("/api/pay", {
            method: "post"
        }).then(res => res.json()).then(data => {
            if (data.status === 200) {
                alert("Thanh toán thành công!");
                location.reload();
            }
        })
    }
}

function addComment(productId) {
    fetch(`/api/products/${productId}/comments`, {
        method: "post",
        body: JSON.stringify({
            "content": document.getElementById("comment").value
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(c => {
        let html = `
          <li class="list-group-item">
              <div class="row">
                  <div class="col-md-1">
                      <img src="${ c.user.avatar }" class="img-fluid rounded-circle" />
                  </div>
                  <div class="col-md-11">
                      <p>${ c.content }</p>
                      <p class="date">${ moment(c.created_date).locale("vi").fromNow() }</p>
                  </div>
              </div>
          </li>
        `
        let e = document.getElementById("comments");
        e.innerHTML = html + e.innerHTML;
    })

}