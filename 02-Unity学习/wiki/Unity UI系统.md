---
created: 2026-07-30
tags: [Unity, UI]
aliases: [UGUI, UI Toolkit]
---

# Unity UI 系统（UGUI）

## 核心概念

### Canvas
- **Screen Space - Overlay**: 始终最上层（默认）
- **Screen Space - Camera**: 相机渲染，可加特效
- **World Space**: 3D 空间 UI（血条、对话气泡）

### RectTransform
- **Anchor**: 父级参考点（四角缩进式定位）
- **Pivot**: 自身旋转/缩放中心点
- **offsetMin/offsetMax**: 相对于 Anchor 的边距

### 常用组件
TextMeshPro / Image / Button / Slider / ScrollRect / Layout Group

### 响应式策略
Canvas Scaler (Scale With Screen Size) + Anchor 预设 + Layout Group

## 生产级代码

### 1. UI 管理器（单例 + 生命周期）

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace GameFramework.UI
{
    public sealed class UIManager : MonoBehaviour
    {
        public static UIManager Instance { get; private set; }

        [SerializeField] private Canvas _mainCanvas;
        [SerializeField] private RectTransform _uiRoot;
        [SerializeField] private float _defaultFadeDuration = 0.3f;

        private readonly Stack<UIView> _viewStack = new();
        private readonly Dictionary<Type, UIView> _cachedViews = new();

        private void Awake()
        {
            if (Instance != null)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            if (_mainCanvas == null)
                _mainCanvas = GetComponentInChildren<Canvas>();
            if (_uiRoot == null)
                _uiRoot = _mainCanvas?.GetComponent<RectTransform>();
        }

        public T Show<T>(bool cached = true) where T : UIView
        {
            var type = typeof(T);

            if (_cachedViews.TryGetValue(type, out var cachedView))
            {
                cachedView.gameObject.SetActive(true);
                cachedView.OnShow();
                _viewStack.Push(cachedView);
                return cachedView as T;
            }

            var view = CreateView<T>();
            if (cached)
                _cachedViews[type] = view;

            _viewStack.Push(view);
            return view;
        }

        private T CreateView<T>() where T : UIView
        {
            var prefab = Resources.Load<T>($"UI/Views/{typeof(T).Name}");
            if (prefab == null)
                throw new Exception($"UI prefab not found: {typeof(T).Name}");

            var instance = Instantiate(prefab, _uiRoot);
            instance.OnCreate();
            instance.OnShow();
            return instance;
        }

        public void HideTopView()
        {
            if (_viewStack.Count == 0) return;
            var view = _viewStack.Pop();
            view.OnHide();
            view.gameObject.SetActive(false);
        }

        public void HideAll()
        {
            while (_viewStack.Count > 0)
                HideTopView();
        }

        public T GetView<T>() where T : UIView
        {
            var type = typeof(T);
            return _cachedViews.TryGetValue(type, out var view) ? view as T : null;
        }

        public bool IsViewActive<T>() where T : UIView
        {
            var type = typeof(T);
            return _cachedViews.ContainsKey(type) && _cachedViews[type].gameObject.activeInHierarchy;
        }

        public Coroutine FadeIn(CanvasGroup group, Action callback = null)
        {
            return StartCoroutine(FadeAlpha(group, 0, 1, _defaultFadeDuration, callback));
        }

        public Coroutine FadeOut(CanvasGroup group, Action callback = null)
        {
            return StartCoroutine(FadeAlpha(group, 1, 0, _defaultFadeDuration, callback));
        }

        private IEnumerator FadeAlpha(CanvasGroup group, float from, float to, float duration, Action callback)
        {
            var elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                group.alpha = Mathf.Lerp(from, to, elapsed / duration);
                yield return null;
            }
            group.alpha = to;
            callback?.Invoke();
        }
    }

    public abstract class UIView : MonoBehaviour
    {
        public virtual void OnCreate() {}
        public virtual void OnShow() {}
        public virtual void OnHide() {}
    }
}
```

### 2. 按钮冷却组件

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace GameFramework.UI
{
    [RequireComponent(typeof(Button))]
    public sealed class ButtonCooldown : MonoBehaviour
    {
        [SerializeField] private float _cooldownDuration = 1f;
        [SerializeField] private bool _showCooldownText = true;
        [SerializeField] private string _cooldownFormat = "F1";

        private Button _button;
        private TextMeshProUGUI _buttonText;
        private string _originalText;
        private bool _isOnCooldown;

        private void Awake()
        {
            _button = GetComponent<Button>();
            _buttonText = GetComponentInChildren<TextMeshProUGUI>();
            if (_buttonText != null)
                _originalText = _buttonText.text;
        }

        private void OnEnable()
        {
            _button.onClick.AddListener(StartCooldown);
        }

        private void OnDisable()
        {
            _button.onClick.RemoveListener(StartCooldown);
        }

        private void StartCooldown()
        {
            if (_isOnCooldown) return;
            StartCoroutine(CooldownRoutine());
        }

        private IEnumerator CooldownRoutine()
        {
            _isOnCooldown = true;
            _button.interactable = false;

            var remaining = _cooldownDuration;
            while (remaining > 0)
            {
                if (_showCooldownText && _buttonText != null)
                    _buttonText.text = remaining.ToString(_cooldownFormat);

                remaining -= Time.deltaTime;
                yield return null;
            }

            if (_showCooldownText && _buttonText != null)
                _buttonText.text = _originalText;

            _button.interactable = true;
            _isOnCooldown = false;
        }

        public void SetCooldown(float duration)
        {
            _cooldownDuration = Mathf.Max(0f, duration);
        }

        public void ResetCooldown()
        {
            StopAllCoroutines();
            _isOnCooldown = false;
            _button.interactable = true;
            if (_buttonText != null)
                _buttonText.text = _originalText;
        }
    }
}
```

### 3. 动态列表（对象池复用）

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

namespace GameFramework.UI
{
    public sealed class DynamicList<T> where T : MonoBehaviour
    {
        private readonly T _itemPrefab;
        private readonly Transform _parent;
        private readonly Queue<T> _pool = new();
        private readonly List<T> _active = new();

        private const int DefaultPoolSize = 10;

        public DynamicList(T prefab, Transform parent, int prewarm = DefaultPoolSize)
        {
            _itemPrefab = prefab;
            _parent = parent;
            Prewarm(prewarm);
        }

        public int ActiveCount => _active.Count;
        public int PooledCount => _pool.Count;

        public IReadOnlyList<T> ActiveItems => _active.AsReadOnly();

        private void Prewarm(int count)
        {
            for (int i = 0; i < count; i++)
            {
                var item = UnityEngine.Object.Instantiate(_itemPrefab, _parent);
                item.gameObject.SetActive(false);
                _pool.Enqueue(item);
            }
        }

        public T Get()
        {
            T item;

            if (_pool.Count > 0)
            {
                item = _pool.Dequeue();
            }
            else
            {
                item = UnityEngine.Object.Instantiate(_itemPrefab, _parent);
            }

            item.gameObject.SetActive(true);
            _active.Add(item);
            return item;
        }

        public void Release(T item)
        {
            if (!_active.Remove(item)) return;

            item.gameObject.SetActive(false);
            item.transform.SetAsLastSibling();
            _pool.Enqueue(item);
        }

        public void ReleaseAll()
        {
            foreach (var item in _active)
            {
                item.gameObject.SetActive(false);
                item.transform.SetAsLastSibling();
                _pool.Enqueue(item);
            }
            _active.Clear();
        }

        public void DestroyPool()
        {
            ReleaseAll();
            foreach (var item in _pool)
                UnityEngine.Object.Destroy(item.gameObject);
            _pool.Clear();
        }
    }
}
```

### 4. 拖拽处理器

```csharp
using UnityEngine;
using UnityEngine.EventSystems;

namespace GameFramework.UI
{
    [RequireComponent(typeof(RectTransform))]
    public sealed class DragHandler : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
    {
        [SerializeField] private bool _clampToScreen = true;
        [SerializeField] private float _returnDuration = 0.3f;

        private RectTransform _rectTransform;
        private Canvas _canvas;
        private Vector2 _originalPosition;
        private Vector2 _dragOffset;
        private bool _isDragging;

        public event System.Action OnDragBegin;
        public event System.Action<Vector2> OnDragging;
        public event System.Action OnDragEnd;
        public event System.Action OnDragCancel;

        public bool IsDragging => _isDragging;

        private void Awake()
        {
            _rectTransform = GetComponent<RectTransform>();
            _canvas = GetComponentInParent<Canvas>();
            _originalPosition = _rectTransform.anchoredPosition;
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            _isDragging = true;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                _rectTransform, eventData.position, _canvas.worldCamera, out _dragOffset);
            OnDragBegin?.Invoke();
        }

        public void OnDrag(PointerEventData eventData)
        {
            if (!_isDragging) return;

            if (RectTransformUtility.ScreenPointToLocalPointInRectangle(
                _rectTransform.parent as RectTransform, eventData.position,
                _canvas.worldCamera, out var localPoint))
            {
                _rectTransform.anchoredPosition = localPoint - _dragOffset;

                if (_clampToScreen)
                    ClampToScreen();

                OnDragging?.Invoke(_rectTransform.anchoredPosition);
            }
        }

        public void OnEndDrag(PointerEventData eventData)
        {
            _isDragging = false;
            OnDragEnd?.Invoke();
        }

        public void ReturnToOriginal()
        {
            StopAllCoroutines();
            StartCoroutine(AnimateReturn());
        }

        private System.Collections.IEnumerator AnimateReturn()
        {
            var start = _rectTransform.anchoredPosition;
            var elapsed = 0f;

            while (elapsed < _returnDuration)
            {
                elapsed += Time.deltaTime;
                var t = Mathf.SmoothStep(0, 1, elapsed / _returnDuration);
                _rectTransform.anchoredPosition = Vector2.Lerp(start, _originalPosition, t);
                yield return null;
            }

            _rectTransform.anchoredPosition = _originalPosition;
        }

        private void ClampToScreen()
        {
            var canvasRect = (_canvas.transform as RectTransform).rect;
            var rect = _rectTransform.rect;

            var pos = _rectTransform.anchoredPosition;
            pos.x = Mathf.Clamp(pos.x, canvasRect.xMin + rect.width * _rectTransform.pivot.x,
                canvasRect.xMax - rect.width * (1 - _rectTransform.pivot.x));
            pos.y = Mathf.Clamp(pos.y, canvasRect.yMin + rect.height * _rectTransform.pivot.y,
                canvasRect.yMax - rect.height * (1 - _rectTransform.pivot.y));

            _rectTransform.anchoredPosition = pos;
        }

        public void ResetPosition()
        {
            _rectTransform.anchoredPosition = _originalPosition;
        }

        public void SetDraggable(bool draggable)
        {
            enabled = draggable;
            if (!draggable && _isDragging)
            {
                _isDragging = false;
                OnDragCancel?.Invoke();
            }
        }
    }
}
```

## 相关链接
- [[Unity 动画系统]]
- [[Unity 性能优化]]

## 来源
- 原始资料：[[raw/2026-07-30-Unity中级学习路径]]
