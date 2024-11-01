var receiptHtml;

$(document).ready(function() {
 // Product search functionality
$(document).ready(function() {
// Product search functionality
$('#product-search').on('input', function() {
  var searchTerm = $(this).val();
  var page = 1;
  $.ajax({
    url: "{% url 'pos:search_products' %}", // Replace with the actual URL
    type: 'GET',
    data: {
      search_term: searchTerm,
      page: page
    },
    success: function(data) {
      $('#product-grid').empty(); // Clear the grid container
      for (var i = 0; i < data.results.length; i++) {
        var product = data.results[i];
        var qtyBadgeClass = '';
        if (product.quantity < 3) {
          qtyBadgeClass = 'badge-danger';
        } else if (product.quantity >= 3 && product.quantity < 6) {
          qtyBadgeClass = 'badge-warning';
        } else {
          qtyBadgeClass = 'badge-success';
        }
        $('#product-grid').append(
          '<div class="col-md-4 col-sm-8 col-xs-12">' + // Grid column classes
          '<div class="card card-sm product-card">' +
          '<div class="card-body">' +
          '<h3 class="card-title text-truncate">' + product.name + '</h3>' +
          '<p class="card-text text-truncate">Category: ' + product.category + '</p>' +
          '<p class="card-text text-truncate">Make: ' + product.make + '</p>' +
          '<p class="card-text text-truncate">Model: ' + product.model + '</p>' +
          '<p class="card-text">In Stock: <span class="badge ' + qtyBadgeClass + '">' + product.quantity + '</span></p>' +
          '<div class="d-flex justify-content-between align-items-center">' +
          '<input type="number" class="quantity-input form-control form-control-sm" value="1" style="width: 50px;">' +
          '<button class="btn btn-success add-to-sale" data-product-id="' + product.id +  '" data-product-quantity="' + product.quantity + '" data-product-name="' + product.name + '">Add to Sale</button>' +
          '</div>' +
          '</div>' +
          '</div>' +
          '</div>'
        );
      }

      // Display pagination links
      var paginationHtml = '';
      if (data.has_previous) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="#" data-page="' + data.previous_page_number + '">Previous</a></li>';
      }
      paginationHtml += '<li class="page-item active"><a class="page-link" href="#">' + page + '</a></li>';
      if (data.has_next) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="#" data-page="' + data.next_page_number + '">Next</a></li>';
      }
      $('#pagination-container ul').html(paginationHtml);

      // Handle pagination link clicks
      $('#pagination-container ul li a').on('click', function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        if (page) {
          $.ajax({
            url: "{% url 'pos:search_products' %}", // Replace with the actual URL
            type: 'GET',
            data: {
              search_term: searchTerm,
              page: page
            },
            success: function(data) {
              $('#product-grid').empty(); // Clear the grid container
              for (var i = 0; i < data.results.length; i++) {
                var product = data.results[i];
                var qtyBadgeClass = '';
                if (product.quantity < 3) {
                  qtyBadgeClass = 'badge-danger';
                } else if (product.quantity >= 3 && product.quantity < 6) {
                  qtyBadgeClass = 'badge-warning';
                } else {
                  qtyBadgeClass = 'badge-success';
                }
                $('#product-grid').append(
                        '<div class="col-md-4 col-sm-8 col-xs-12">' + // Grid column classes
                '<div class="card card-sm product-card">' +
                '<div class="card-body">' +
                '<h3 class="card-title text-truncate">' + product.name + '</h3>' +
                '<p class="card-text text-truncate">Category: ' + product.category + '</p>' +
                '<p class="card-text text-truncate">Make: ' + product.make + '</p>' +
                '<p class="card-text text-truncate">Model: ' + product.model + '</p>' +
                '<p class="card-text">In Stock: <span class="badge ' + qtyBadgeClass + '">' + product.quantity + '</span></p>' +
                '<div class="d-flex justify-content-between align-items-center">' +
                '<input type="number" class="quantity-input form-control form-control-sm" value="1" style="width: 50px;">' +
                '<button class="btn btn-success add-to-sale" data-product-id="' + product.id +  '" data-product-quantity="' + product.quantity + '" data-product-name="' + product.name + '">Add to Sale</button>' +
                '</div>' +
                '</div>' +
                '</div>' +
                '</div>'
                );
              }

              // Display pagination links
              var paginationHtml = '';
              if (data.has_previous) {
                paginationHtml += '<li class="page-item"><a class="page-link" href="#" data-page="' + data.previous_page_number + '">Previous</a></li>';
              }
              paginationHtml += '<li class="page-item active"><a class="page-link" href="#">' + page + '</a></li>';
              if (data.has_next) {
                paginationHtml += '<li class="page-item"><a class="page-link" href="#" data-page="' + data.next_page_number + '">Next</a></li>';
              }
              $('#pagination-container ul').html(paginationHtml);
            }
          });
        }
      });
    }
  });
});
});



// Add product to sale
$(document).on('click', '.add-to-sale', function() {
var productId = $(this).data('product-id');
var productQuantity = $(this).data('product-quantity'); // Get the product quantity
var saleId = $('#sale-id').val(); // Get the sale ID from the hidden input field
var quantity = $(this).closest('.card').find('.quantity-input').val(); // Get the quantity from the input field
var existingRow = $('#sale-table-body tr').find('td:nth-child(1):contains("' + $(this).data('product-name') + '")').closest('tr');
if (existingRow.length > 0) {
  var existingQuantityInput = existingRow.find('td:nth-child(2) input');
  var existingQuantity = parseInt(existingQuantityInput.val());
  var newQuantity = existingQuantity + parseInt(quantity);
  if (newQuantity <= productQuantity) {
    existingQuantityInput.val(newQuantity);
    var price = existingRow.find('td:nth-child(3)').text();
    existingRow.find('td:nth-child(4) span').text(total.toFixed(2));
    updateTotal();
  } else {
    alert('Product quantity exceeded');
  }
} else {
  if (saleId) {
    $.ajax({
      url: "{% url 'pos:add_product_to_sale'%}",
      type: 'POST',
      data: {
        product_id: productId,
        quantity: quantity,
        sale_id: saleId
      },
      headers: {
        'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
      },
      success: function(data) {
        // Update the sale table and total amount
        $('#sale-table-body').html(data.sale_table);
        $('#total').text(data.total_amount);
        console.log(data); // Log the response from the server
        // Show the complete sale button
        $('.complete-sale-btn').show();
        $('#amount-paid').show();
      }
    });
  } else {
    // Create a new sale if there is no sale_id
    $.ajax({
      url: "{% url 'pos:create_sale'%}",
      type: 'POST',
      headers: {
        'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
      },
      success: function(data) {
        // Get the new sale_id
        var newSaleId = data.sale_id;
        // Update the sale_id input field
        $('#sale-id').val(newSaleId);
        // Add the product to the new sale
        $.ajax({
          url: "{% url 'pos:add_product_to_sale'%}",
          type: 'POST',
          data: {
            product_id: productId,
            quantity: quantity,
            sale_id: newSaleId
          },
          headers: {
            'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
          },
          success: function(data) {
            // Update the sale table and total amount
            $('#sale-table-body').html(data.sale_table);
            $('#total').text(data.total_amount);
            console.log(data); // Log the response from the server
            // Show the complete sale button
            $('.complete-sale-btn').show();
            $('#amount-paid').show();
          }
        });
      }
    });
  }
}
});



// Update total when quantity changes
  $(document).on('input', '.quantity-input', function() {
var quantity = $(this).val();
var price = $(this).data('price');
var total = quantity * price;
$(this).closest('tr').find('td:nth-child(4) span').text(total);
updateTotal();

// Update the quantity of the sale item
var productId = $(this).attr('id').split('_')[1];
var saleId = $('#sale-id').val();
$.ajax({
  url: "",
  type: 'POST',
  data: {
    product_id: productId,
    quantity: quantity,
    sale_id: saleId,
    

  },
  headers: {
    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
  },
  success: function(data) {
    console.log(data);
  }
});
});

  // Update total when quantity changes
  function updateTotal() {
    var total = 0;
    $('#sale-table-body tr').each(function() {
      var totalCell = $(this).find('td:nth-child(4) span');
      var totalText = totalCell.text();
      if (totalText !== '') {
        total += parseFloat(totalText);
      }
    });
    $('#total').text(total.toFixed(2));

  }
  
// Complete sale
$(document).on('click', '.complete-sale-btn', function() {
var saleId = $('#sale-id').val();
var amountPaid = parseFloat($('#amount-paid').val()); // Parse as float
var total = parseFloat($('#total').text()); // Parse total as float

$.ajax({
  url: "{% url 'pos:complete_sale' %}",
  type: 'POST',
  data: {
    sale_id: saleId,
    amount_paid: amountPaid,
  },
  headers: {
    'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
  },
  success: function(data) {
    // Update the sale table and total amount
    $('#sale-table-body').html('');
    $('#total').text('0.00');
    // Store the receipt HTML in a variable
    receiptHtml = data.receipt_html;
    // Show the sale completed modal
    $('#saleCompletedModal').modal('show');
    // You can also redirect the user to the sale list page
    window.location.href = "{% url 'pos:sale_list' %}";
  }
});
});
  // Remove product from sale
  $(document).on('click', '.remove-from-sale', function() {
    var productId = $(this).data('product-id');
    var saleId = $('#sale-id').val();
    $.ajax({
      url: "{% url 'pos:remove_product_from_sale' %}",
      type: 'POST',
      data: {
        product_id: productId,
        sale_id: saleId
      },
      headers: {
        'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
      },
      success: function(data) {
        // Update the sale table and total amount
        $('#sale-table-body').html(data.sale_table);
        $('#total').text(data.total_amount);
      }
    });
  });

  // Show receipt modal after sale completed modal
  $('#show-receipt-modal').on('click', function() {
    $('#saleCompletedModal').modal('hide');
    $('#receiptModal').modal ('show');
    // Use the stored receipt HTML
    $('#receipt-body').html(receiptHtml);
  });

  // Print receipt button
  $('#print-receipt-btn').on('click', function() {
    var receiptHtml = $('#receipt-body').html();
    var printWindow = window.open('', '_blank ');
    printWindow.document.write(receiptHtml);
    printWindow.print();
  });

  // Save receipt button
  $('#save-receipt-btn').on('click', function() {
    var receiptHtml = $('#receipt-body').html();
    var blob = new Blob([receiptHtml], {
      type: 'text/html'
    });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'receipt.html';
    a.click();
  });
});