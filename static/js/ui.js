document.addEventListener("DOMContentLoaded", () => {
document.querySelectorAll(".card").forEach(c => {
c.classList.add("fade-slide");
});
});

// ========== ГЛОБАЛЬНЫЕ ФУНКЦИИ ==========

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initCartFunctions();
    initProductGallery();
    initAccordions();
    initForms();
    initQuantityControls();
    initMobileMenu();
    initScrollEffects();
    initNotifications();
    initLazyLoading();
    initRatingSystem();
});

// ========== КОРЗИНА ==========

function initCartFunctions() {
    // Добавление в корзину с AJAX
    document.querySelectorAll('.btn-add-to-cart').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            addToCart(productId);
        });
    });

    // Обновление количества в корзине
    document.querySelectorAll('.cart-quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.dataset.productId;
            const quantity = parseInt(this.value);
            updateCartQuantity(productId, quantity);
        });
    });

    // Кнопки увеличения/уменьшения количества
    document.querySelectorAll('.btn-quantity-dec, .btn-quantity-inc').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.cart-quantity-input');
            const productId = input.dataset.productId;
            let quantity = parseInt(input.value);
            
            if (this.classList.contains('btn-quantity-dec')) {
                quantity = Math.max(1, quantity - 1);
            } else {
                quantity = quantity + 1;
            }
            
            input.value = quantity;
            updateCartQuantity(productId, quantity);
        });
    });

    // Удаление из корзины
    document.querySelectorAll('.btn-remove-from-cart').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            if (confirm('Видалити цей товар з кошика?')) {
                removeFromCart(productId);
            }
        });
    });
}

function addToCart(productId) {
    showLoading();
    
    fetch(`/add_to_cart/${productId}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showNotification('Товар додано до кошика!', 'success');
            
            // Обновляем иконку корзины в навбаре
            const cartBadge = document.querySelector('.cart-badge');
            if (cartBadge) {
                cartBadge.textContent = data.cart_count;
                cartBadge.classList.remove('d-none');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Помилка при додаванні до кошика', 'error');
    })
    .finally(() => {
        hideLoading();
    });
}

function updateCartQuantity(productId, quantity) {
    fetch('/api/update_quantity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            updateCartTotal();
            showNotification('Кількість оновлено', 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Помилка при оновленні', 'error');
    });
}

function removeFromCart(productId) {
    fetch(`/delete_from_cart/${productId}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Помилка при видаленні', 'error');
    });
}

function updateCartCount(count) {
    // Обновляем все счетчики корзины на странице
    document.querySelectorAll('.cart-count').forEach(element => {
        element.textContent = count;
    });
    
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        if (count > 0) {
            cartBadge.textContent = count;
            cartBadge.classList.remove('d-none');
        } else {
            cartBadge.classList.add('d-none');
        }
    }
}

function updateCartTotal() {
    fetch('/api/cart_info')
    .then(response => response.json())
    .then(data => {
        // Обновляем отображение общей суммы
        document.querySelectorAll('.cart-total').forEach(element => {
            element.textContent = `${data.total} ₴`;
        });
        
        // Обновляем количество товаров в мини-корзине
        const miniCart = document.querySelector('.mini-cart');
        if (miniCart) {
            miniCart.innerHTML = '';
            
            if (data.items.length > 0) {
                data.items.forEach(item => {
                    const cartItem = document.createElement('div');
                    cartItem.className = 'mini-cart-item';
                    cartItem.innerHTML = `
                        <div class="d-flex align-items-center">
                            <img src="/static/img/${item.image || 'placeholder.png'}" 
                                 alt="${item.name}" 
                                 class="mini-cart-img">
                            <div class="ms-2">
                                <div class="mini-cart-title">${item.name}</div>
                                <div class="mini-cart-price">${item.qty} × ${item.price} ₴</div>
                            </div>
                        </div>
                    `;
                    miniCart.appendChild(cartItem);
                });
                
                const totalEl = document.createElement('div');
                totalEl.className = 'mini-cart-total';
                totalEl.innerHTML = `
                    <div class="d-flex justify-content-between">
                        <strong>Всього:</strong>
                        <strong>${data.total} ₴</strong>
                    </div>
                    <a href="/cart" class="btn btn-primary btn-sm w-100 mt-2">Оформити замовлення</a>
                `;
                miniCart.appendChild(totalEl);
            } else {
                miniCart.innerHTML = '<div class="text-center py-3 text-muted">Кошик порожній</div>';
            }
        }
    });
}

// ========== ГАЛЕРЕЯ ТОВАРА ==========

function initProductGallery() {
    const mainImage = document.getElementById('mainProductImage');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    
    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                // Меняем основное изображение
                mainImage.src = this.src;
                mainImage.alt = this.alt;
                
                // Обновляем активный класс
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Плавное появление
                mainImage.style.opacity = '0';
                setTimeout(() => {
                    mainImage.style.opacity = '1';
                }, 100);
            });
        });
        
        // Zoom эффект
        mainImage.addEventListener('mousemove', function(e) {
            if (window.innerWidth > 768) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const xPercent = x / rect.width * 100;
                const yPercent = y / rect.height * 100;
                
                this.style.transformOrigin = `${xPercent}% ${yPercent}%`;
                this.style.transform = 'scale(1.5)';
            }
        });
        
        mainImage.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.transformOrigin = 'center center';
        });
        
        // Модальное окно для полноразмерного изображения
        mainImage.addEventListener('click', function() {
            if (window.innerWidth > 768) {
                const modalHTML = `
                    <div class="modal fade" id="imageModal" tabindex="-1">
                        <div class="modal-dialog modal-dialog-centered modal-xl">
                            <div class="modal-content bg-transparent border-0">
                                <div class="modal-body p-0">
                                    <img src="${this.src}" alt="${this.alt}" class="img-fluid">
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHTML);
                const modal = new bootstrap.Modal(document.getElementById('imageModal'));
                modal.show();
                
                // Удаляем модальное окно после закрытия
                document.getElementById('imageModal').addEventListener('hidden.bs.modal', function() {
                    this.remove();
                });
            }
        });
    }
}

// ========== АККОРДЕОНЫ И ТАБЫ ==========

function initAccordions() {
    // Сохраняем активный таб при перезагрузке
    const productTabs = document.querySelector('#productTabs');
    if (productTabs) {
        const activeTab = localStorage.getItem('activeProductTab');
        if (activeTab) {
            const tabTrigger = document.querySelector(`#${activeTab}`);
            if (tabTrigger) {
                new bootstrap.Tab(tabTrigger).show();
            }
        }
        
        productTabs.addEventListener('shown.bs.tab', function(event) {
            localStorage.setItem('activeProductTab', event.target.id);
        });
    }
    
    // Анимация аккордеонов
    document.querySelectorAll('.accordion-button').forEach(button => {
        button.addEventListener('click', function() {
            const icon = this.querySelector('.accordion-icon');
            if (icon) {
                if (this.classList.contains('collapsed')) {
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-up');
                } else {
                    icon.classList.remove('bi-chevron-up');
                    icon.classList.add('bi-chevron-down');
                }
            }
        });
    });
}

// ========== ФОРМЫ ==========

function initForms() {
    // Валидация форм
    document.querySelectorAll('.needs-validation').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Показываем все ошибки
                const invalidFields = form.querySelectorAll(':invalid');
                invalidFields.forEach(field => {
                    field.classList.add('is-invalid');
                    
                    // Прокручиваем к первой ошибке
                    if (invalidFields[0] === field) {
                        field.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                    }
                });
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Маска телефона
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 9) value = value.substring(0, 9);
            
            let formatted = '';
            if (value.length > 0) formatted = value.substring(0, 2);
            if (value.length > 2) formatted += ' ' + value.substring(2, 5);
            if (value.length > 5) formatted += ' ' + value.substring(5, 7);
            if (value.length > 7) formatted += ' ' + value.substring(7, 9);
            
            e.target.value = formatted;
        });
    });
    
    // Автодополнение города
    const cityInput = document.getElementById('city');
    if (cityInput) {
        const popularCities = ['Київ', 'Харків', 'Одеса', 'Дніпро', 'Львів', 'Запоріжжя'];
        
        cityInput.addEventListener('input', function(e) {
            const value = e.target.value.toLowerCase();
            if (value.length > 1) {
                const datalist = document.createElement('datalist');
                datalist.id = 'city-suggestions';
                
                popularCities.forEach(city => {
                    if (city.toLowerCase().includes(value)) {
                        const option = document.createElement('option');
                        option.value = city;
                        datalist.appendChild(option);
                    }
                });
                
                const existingDatalist = document.getElementById('city-suggestions');
                if (existingDatalist) {
                    existingDatalist.remove();
                }
                
                if (datalist.children.length > 0) {
                    cityInput.setAttribute('list', 'city-suggestions');
                    document.body.appendChild(datalist);
                }
            }
        });
    }
}

// ========== КОНТРОЛЫ КОЛИЧЕСТВА ==========

function initQuantityControls() {
    document.querySelectorAll('.quantity-control').forEach(control => {
        const input = control.querySelector('.quantity-input');
        const minusBtn = control.querySelector('.quantity-minus');
        const plusBtn = control.querySelector('.quantity-plus');
        
        if (input && minusBtn && plusBtn) {
            minusBtn.addEventListener('click', () => {
                let value = parseInt(input.value) || 1;
                if (value > parseInt(input.min || 1)) {
                    input.value = value - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            plusBtn.addEventListener('click', () => {
                let value = parseInt(input.value) || 1;
                const max = parseInt(input.max) || 99;
                if (value < max) {
                    input.value = value + 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            input.addEventListener('change', () => {
                let value = parseInt(input.value) || 1;
                const min = parseInt(input.min) || 1;
                const max = parseInt(input.max) || 99;
                
                if (value < min) input.value = min;
                if (value > max) input.value = max;
            });
        }
    });
}

// ========== МОБИЛЬНОЕ МЕНЮ ==========

function initMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Закрытие меню при клике на ссылку
        navbarCollapse.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    }
                }
            });
        });
    }
}

// ========== ЭФФЕКТЫ ПРИ СКРОЛЛЕ ==========

function initScrollEffects() {
    // Плавный скролл
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Появление элементов при скролле
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Наблюдаем за карточками товаров
    document.querySelectorAll('.product-card, .category-card').forEach(card => {
        observer.observe(card);
    });
    
    // Sticky header
    const header = document.querySelector('.navbar');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                header.classList.add('navbar-scrolled');
            } else {
                header.classList.remove('navbar-scrolled');
            }
        });
    }
}

// ========== УВЕДОМЛЕНИЯ ==========

function initNotifications() {
    // Создаем контейнер для уведомлений
    const notificationContainer = document.createElement('div');
    notificationContainer.className = 'notification-container';
    document.body.appendChild(notificationContainer);
}

function showNotification(message, type = 'info', duration = 3000) {
    const container = document.querySelector('.notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="bi ${type === 'success' ? 'bi-check-circle' : type === 'error' ? 'bi-exclamation-circle' : 'bi-info-circle'} me-2"></i>
            ${message}
        </div>
        <button class="notification-close">
            <i class="bi bi-x"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Закрытие по кнопке
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        closeNotification(notification);
    });
    
    // Автоматическое закрытие
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notification);
        }, duration);
    }
    
    return notification;
}

function closeNotification(notification) {
    notification.classList.remove('show');
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// ========== LAZY LOADING ==========

function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img.lazy').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// ========== СИСТЕМА РЕЙТИНГА ==========

function initRatingSystem() {
    document.querySelectorAll('.rating-input').forEach(ratingInput => {
        const stars = ratingInput.querySelectorAll('input[type="radio"]');
        const labels = ratingInput.querySelectorAll('label');
        
        labels.forEach(label => {
            label.addEventListener('mouseenter', function() {
                const value = parseInt(this.getAttribute('for').replace('star', ''));
                highlightStars(value);
            });
            
            label.addEventListener('mouseleave', function() {
                const checkedStar = ratingInput.querySelector('input:checked');
                if (checkedStar) {
                    highlightStars(parseInt(checkedStar.value));
                } else {
                    resetStars();
                }
            });
            
            label.addEventListener('click', function() {
                const value = parseInt(this.getAttribute('for').replace('star', ''));
                highlightStars(value);
            });
        });
        
        function highlightStars(value) {
            labels.forEach((label, index) => {
                if (index < value) {
                    label.querySelector('i').classList.add('bi-star-fill');
                    label.querySelector('i').classList.remove('bi-star');
                } else {
                    label.querySelector('i').classList.add('bi-star');
                    label.querySelector('i').classList.remove('bi-star-fill');
                }
            });
        }
        
        function resetStars() {
            labels.forEach(label => {
                label.querySelector('i').classList.add('bi-star');
                label.querySelector('i').classList.remove('bi-star-fill');
            });
        }
    });
}

// ========== УТИЛИТЫ ==========

function showLoading() {
    let loading = document.querySelector('.loading-overlay');
    if (!loading) {
        loading = document.createElement('div');
        loading.className = 'loading-overlay';
        loading.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Завантаження...</span>
            </div>
        `;
        document.body.appendChild(loading);
    }
    loading.classList.add('active');
}

function hideLoading() {
    const loading = document.querySelector('.loading-overlay');
    if (loading) {
        loading.classList.remove('active');
        setTimeout(() => {
            if (loading.parentNode && !loading.classList.contains('active')) {
                loading.parentNode.removeChild(loading);
            }
        }, 300);
    }
}

// Дебаунс для частых событий
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Форматирование цены
function formatPrice(price) {
    return new Intl.NumberFormat('uk-UA', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

// ========== ГЛОБАЛЬНЫЙ ЭКСПОРТ ==========

// Делаем функции доступными глобально
window.SBGear = {
    addToCart,
    updateCartQuantity,
    removeFromCart,
    showNotification,
    formatPrice,
    debounce
};