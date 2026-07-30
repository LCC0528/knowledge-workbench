---
created: 2026-07-30
tags: [Unity, 优化]
aliases: [Performance, Optimization]
---

# Unity 性能优化

## 核心概念

### 渲染优化

| 技术 | 原理 | 适用场景 |
|------|------|----------|
| 静态批处理 | 合并同材质静态物体 | 场景装饰物 |
| 动态批处理 | 运行时合并小网格 | 小物体（<300顶点） |
| GPU Instancing | 一次绘制多个相同模型 | 大量重复物体（树、草） |
| LOD | 距离远时用低模替代 | 角色、建筑 |
| Occlusion Culling | 遮挡时跳过渲染 | 室内场景 |

### CPU 优化
- **对象池**: 复用 GameObject 而非 Instantiate/Destroy
- **协程 / Job System**: 分散耗时计算
- **Profile 慢函数**: 用 Profiler 定位热点

### 内存优化
- **AssetBundle 分包**: 按场景/功能拆分资源
- **Resources 目录**: 避免滥用，改用 Addressables
- **纹理压缩**: ASTC (移动) / DXT (PC) / ETC2
- **音频压缩**: Vorbis / ADPCM / 强制单声道

### 工具链
- **Profiler**: CPU/GPU/Memory 时间线分析
- **Frame Debugger**: 逐帧查看 Draw Call
- **Memory Profiler**: 快照对比内存泄漏
- **RenderDoc**: GPU 调试

### 生产级代码

#### 1. 对象池 (泛型, 线程安全)

```csharp
using System;
using System.Collections.Concurrent;
using UnityEngine;

namespace GameFramework.Optimization
{
    public class ObjectPool<T> : IDisposable where T : Component
    {
        private readonly ConcurrentStack<T> _pool = new();
        private readonly Func<T> _factory;
        private readonly int _maxSize;
        private volatile int _count;

        public event Action<T> OnGet;
        public event Action<T> OnRelease;
        public event Action<T> OnDestroy;
        public int Count => _count;
        public int MaxSize => _maxSize;

        public ObjectPool(Func<T> factory, int preWarm = 0, int maxSize = 100)
        {
            _factory = factory ?? throw new ArgumentNullException(nameof(factory));
            _maxSize = maxSize;
            for (int i = 0; i < preWarm; i++)
            {
                T obj = factory();
                obj.gameObject.SetActive(false);
                _pool.Push(obj);
            }
            _count = preWarm;
        }

        public T Get()
        {
            if (_pool.TryPop(out T obj))
            {
                obj.gameObject.SetActive(true);
                OnGet?.Invoke(obj);
                return obj;
            }
            if (_count < _maxSize)
            {
                T newObj = _factory();
                _count++;
                newObj.gameObject.SetActive(true);
                OnGet?.Invoke(newObj);
                return newObj;
            }
            throw new InvalidOperationException($"Pool of {typeof(T).Name} exhausted (max: {_maxSize})");
        }

        public void Release(T obj)
        {
            if (obj == null) return;
            OnRelease?.Invoke(obj);
            obj.gameObject.SetActive(false);
            _pool.Push(obj);
        }

        public void Dispose()
        {
            while (_pool.TryPop(out T obj))
            {
                OnDestroy?.Invoke(obj);
                if (Application.isPlaying)
                    UnityEngine.Object.Destroy(obj.gameObject);
                else
                    UnityEngine.Object.DestroyImmediate(obj.gameObject);
            }
            _count = 0;
        }
    }
}
```

#### 2. LOD 控制器

```csharp
using System;
using UnityEngine;

namespace GameFramework.Optimization
{
    public class LODController : MonoBehaviour
    {
        [SerializeField] private float[] _distances = { 10f, 30f, 60f };
        [SerializeField] private GameObject[] _lodLevels;
        [SerializeField] private float _cooldown = 0.2f;
        [SerializeField] private Camera _camera;

        public event Action<int> OnLODChanged;

        private int _currentLevel = -1;
        private float _lastSwitchTime;
        private Transform _cameraTransform;

        private void Awake()
        {
            if (_camera == null) _camera = Camera.main;
            _cameraTransform = _camera != null ? _camera.transform : null;
            for (int i = 0; i < _lodLevels.Length; i++)
                _lodLevels[i]?.SetActive(i == 0);
            _currentLevel = 0;
        }

        private void Update()
        {
            if (_cameraTransform == null || _lodLevels == null || _lodLevels.Length == 0)
                return;

            float distance = Vector3.Distance(transform.position, _cameraTransform.position);
            int level = _lodLevels.Length - 1;
            for (int i = 0; i < _distances.Length && i < _lodLevels.Length - 1; i++)
            {
                if (distance < _distances[i])
                {
                    level = i;
                    break;
                }
            }

            if (level != _currentLevel && Time.time >= _lastSwitchTime + _cooldown)
            {
                _lastSwitchTime = Time.time;
                for (int i = 0; i < _lodLevels.Length; i++)
                    _lodLevels[i]?.SetActive(i == level);
                _currentLevel = level;
                OnLODChanged?.Invoke(level);
            }
        }
    }
}
```

#### 3. 帧率管理器

```csharp
using UnityEngine;

namespace GameFramework.Optimization
{
    public class FrameRateManager : MonoBehaviour
    {
        public static FrameRateManager Instance { get; private set; }

        [SerializeField] private bool _batterySaverEnabled = true;
        [SerializeField] private bool _showFPS = false;
        [SerializeField] private int _targetFPS = 60;
        [SerializeField] private int _lowFPSThreshold = 30;

        private float _deltaTime;
        private float _fps;
        private int _qualityLevel;
        private GUIStyle _fpsStyle;

        private void Awake()
        {
            if (Instance != null)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            _qualityLevel = QualitySettings.GetQualityLevel();
            _fpsStyle = new GUIStyle { fontSize = 24, normal = { textColor = Color.green } };
            ApplyPlatformSettings();
        }

        private void ApplyPlatformSettings()
        {
#if UNITY_ANDROID || UNITY_IOS
            if (_batterySaverEnabled)
                _targetFPS = 30;
#endif
            Application.targetFrameRate = _targetFPS;
            QualitySettings.vSyncCount = 0;
        }

        private void Update()
        {
            _deltaTime += (Time.unscaledDeltaTime - _deltaTime) * 0.1f;
            _fps = 1.0f / _deltaTime;

            if (_batterySaverEnabled && _fps < _lowFPSThreshold)
            {
                int lower = Mathf.Max(0, _qualityLevel - 1);
                if (QualitySettings.GetQualityLevel() != lower)
                    QualitySettings.SetQualityLevel(lower, true);
            }
        }

        private void OnGUI()
        {
            if (!_showFPS) return;
            _fpsStyle.normal.textColor = _fps >= 30 ? Color.green : (_fps >= 15 ? Color.yellow : Color.red);
            GUI.Label(new Rect(10, 10, 120, 40), $"FPS: {_fps:F1}", _fpsStyle);
        }

        public void SetBatterySaver(bool enabled)
        {
            _batterySaverEnabled = enabled;
            ApplyPlatformSettings();
        }

        public void ToggleFPS() => _showFPS = !_showFPS;
    }
}
```

#### 4. 内存监控器

```csharp
using System;
using UnityEngine;

namespace GameFramework.Optimization
{
    public class MemoryMonitor : MonoBehaviour
    {
        [SerializeField] private float _logInterval = 10f;
        [SerializeField] private float _warningThresholdMB = 700f;
        [SerializeField] private bool _autoCollect = false;

        public event Action<float> OnMemoryWarning;

        private float _timer;

        private void Update()
        {
            _timer += Time.unscaledDeltaTime;
            if (_timer >= _logInterval)
            {
                _timer = 0f;
                LogMemoryStats();
                if (_autoCollect && GetUsedMB() > _warningThresholdMB)
                {
                    Debug.LogWarning("[MemoryMonitor] Forcing GC Collect");
                    GC.Collect();
                    GC.WaitForPendingFinalizers();
                }
            }
        }

        public float GetUsedMB() => (float)(GC.GetTotalMemory(false)) / (1024f * 1024f);

        public float GetTotalMB()
        {
            float used = GetUsedMB();
#if UNITY_ANDROID && !UNITY_EDITOR
            using (var info = new AndroidJavaObject("android.app.ActivityManager.MemoryInfo"))
            {
                using (var am = new AndroidJavaClass("android.app.ActivityManager"))
                {
                    var ctx = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
                        .GetStatic<AndroidJavaObject>("currentActivity")
                        .Call<AndroidJavaObject>("getSystemService", "activity");
                    am.Call("getMemoryInfo", info);
                    return info.Get<long>("totalMem") / (1024f * 1024f);
                }
            }
#else
            return SystemInfo.systemMemorySize;
#endif
        }

        public float GetAllocatedMB()
        {
            return (float)Profiler. GetTotalAllocatedMemoryLong() / (1024f * 1024f);
        }

        public MemoryStats GetStats()
        {
            return new MemoryStats
            {
                UsedMB = GetUsedMB(),
                TotalMB = GetTotalMB(),
                AllocatedMB = GetAllocatedMB()
            };
        }

        private void LogMemoryStats()
        {
            float used = GetUsedMB();
            float total = GetTotalMB();
            float allocated = GetAllocatedMB();
            Debug.Log($"[MemoryMonitor] Used: {used:F1}MB / Total: {total:F1}MB / Allocated: {allocated:F1}MB");
            if (used > _warningThresholdMB)
            {
                Debug.LogWarning($"[MemoryMonitor] Memory high: {used:F1}MB > {_warningThresholdMB}MB");
                OnMemoryWarning?.Invoke(used);
            }
        }

        public void ForceCollect()
        {
            GC.Collect();
            GC.WaitForPendingFinalizers();
            LogMemoryStats();
        }

        public struct MemoryStats
        {
            public float UsedMB;
            public float TotalMB;
            public float AllocatedMB;
        }
    }
}
```

## 相关链接
- [[Unity 动画系统]]
- [[Unity UI 系统]]

## 来源
- 原始资料：[[raw/2026-07-30-Unity中级学习路径]]