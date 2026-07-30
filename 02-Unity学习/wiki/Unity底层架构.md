---
created: 2026-07-30
tags: [Unity, 架构, 设计模式]
aliases: [Architecture, DOTS, ECS]
---

# Unity 底层架构与设计模式

## 核心概念

### Scriptable Object（核心资产）
- 用作**数据容器**：配置表、关卡数据、角色属性
- 用作**事件通道**：解耦发布者/订阅者
- 优点：可序列化、可复用、编辑器友好

### 设计模式

| 模式 | Unity 中的实现 |
|------|----------------|
| 状态机 (FSM) | 角色行为切换（Idle / Walk / Attack） |
| 对象池 (Object Pool) | 子弹、粒子、敌人复用 |
| 观察者 / 事件 | C# event / UnityEvent / ScriptableObject Event |
| 命令模式 | 撤销系统、输入缓冲 |
| 依赖注入 | Zenject / VContainer 管理依赖 |

### DOTS（Data-Oriented Tech Stack）
- **Entity**: 轻量 ID，替代 GameObject
- **Component**: 纯数据（struct），无方法
- **System**: 处理逻辑，批量操作同构数据
- 适用场景：大量实体（10万+同屏）、物理模拟、RTS

### Addressables
- 替代 Resources / AssetBundle 的现代方案
- 按需加载/卸载、远程资源管理、依赖自动处理

## 相关链接
- [[Unity 性能优化]]
- [[Unity 动画系统]]

## 来源
- 原始资料：[[raw/2026-07-30-Unity中级学习路径]]

### 生产级代码

#### 1. ScriptableObject 事件系统

```csharp
// Assets/Scripts/Core/Events/GameEvent.cs
using UnityEngine;
using UnityEngine.Events;

namespace GameFramework.Core.Events
{
    public abstract class GameEvent<T> : ScriptableObject
    {
        private readonly UnityEvent<T> _evt = new();

        public void Raise(T value) => _evt.Invoke(value);

        public void AddListener(UnityAction<T> listener) => _evt.AddListener(listener);

        public void RemoveListener(UnityAction<T> listener) => _evt.RemoveListener(listener);

        private void OnDisable() => _evt.RemoveAllListeners();
    }

    [CreateAssetMenu(menuName = "GameFramework/Events/FloatEvent", fileName = "FloatEvent")]
    public class FloatEvent : GameEvent<float> { }

    [CreateAssetMenu(menuName = "GameFramework/Events/IntEvent", fileName = "IntEvent")]
    public class IntEvent : GameEvent<int> { }

    [CreateAssetMenu(menuName = "GameFramework/Events/StringEvent", fileName = "StringEvent")]
    public class StringEvent : GameEvent<string> { }

    [CreateAssetMenu(menuName = "GameFramework/Events/VoidEvent", fileName = "VoidEvent")]
    public class VoidEvent : GameEvent<Empty> { }

    [System.Serializable]
    public struct Empty { }
}
```

```csharp
// Assets/Scripts/Core/Events/GameEventListener.cs
using UnityEngine;
using UnityEngine.Events;

namespace GameFramework.Core.Events
{
    public class GameEventListener : MonoBehaviour
    {
        [SerializeField] private VoidEvent _voidEvent;
        [SerializeField] private UnityEvent _onEventRaised;

        private void OnEnable() => _voidEvent?.AddListener(Respond);

        private void OnDisable() => _voidEvent?.RemoveListener(Respond);

        private void Respond() => _onEventRaised.Invoke();
    }

    public class GameEventListener<T> : MonoBehaviour
    {
        [SerializeField] private GameEvent<T> _gameEvent;
        [SerializeField] private UnityEvent<T> _onEventRaised;

        private void OnEnable() => _gameEvent?.AddListener(Respond);

        private void OnDisable() => _gameEvent?.RemoveListener(Respond);

        private void Respond(T value) => _onEventRaised.Invoke(value);
    }
}
```

```csharp
// Assets/Scripts/Core/Events/GameEventRaiseOnStart.cs
using UnityEngine;

namespace GameFramework.Core.Events
{
    public class GameEventRaiseOnStart : MonoBehaviour
    {
        [SerializeField] private VoidEvent _voidEvent;

        private void Start() => _voidEvent?.Raise(default);
    }
}
```

#### 2. 服务定位器 (Service Locator)

```csharp
// Assets/Scripts/Core/Services/ServiceLocator.cs
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GameFramework.Core.Services
{
    public static class ServiceLocator
    {
        private static readonly Dictionary<Type, object> _services = new();
        private static readonly Dictionary<Type, Func<object>> _providers = new();

        public static void Register<T>(T service) where T : class
        {
            var type = typeof(T);
            if (_services.ContainsKey(type))
                Debug.LogWarning($"[ServiceLocator] Service {type.Name} already registered — overwriting.");
            _services[type] = service;
        }

        public static T Get<T>() where T : class
        {
            var type = typeof(T);
            if (_services.TryGetValue(type, out var service))
                return service as T;

            if (_providers.TryGetValue(type, out var provider))
            {
                var instance = provider() as T;
                if (instance != null)
                {
                    _services[type] = instance;
                    return instance;
                }
            }

            Debug.LogError($"[ServiceLocator] Service {type.Name} not registered.");
            return null;
        }

        public static void Remove<T>() where T : class
        {
            _services.Remove(typeof(T));
        }

        public static void RegisterLazy<T>(Func<T> provider) where T : class
        {
            _providers[typeof(T)] = () => provider();
        }

        public static void Clear()
        {
            _services.Clear();
            _providers.Clear();
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Initialize()
        {
            SceneManager.sceneUnloaded += _ => Clear();
        }
    }
}
```

#### 3. 对象工厂 (Factory Pattern)

```csharp
// Assets/Scripts/Core/Factory/IFactory.cs
using UnityEngine;

namespace GameFramework.Core.Factory
{
    public interface IFactory<T>
    {
        T Create();
        void Warmup(int count);
    }

    public class PrefabFactory : IFactory<GameObject>
    {
        private readonly GameObject _prefab;
        private readonly Transform _parent;
        private readonly int _warmupCount;

        public PrefabFactory(GameObject prefab, Transform parent = null, int warmupCount = 0)
        {
            _prefab = prefab;
            _parent = parent;
            _warmupCount = warmupCount;
            if (warmupCount > 0) Warmup(warmupCount);
        }

        public GameObject Create()
        {
            var instance = Object.Instantiate(_prefab, _parent);
            instance.SetActive(true);
            return instance;
        }

        public void Warmup(int count)
        {
            var pool = new System.Collections.Generic.Stack<GameObject>(count);
            for (int i = 0; i < count; i++)
            {
                var go = Object.Instantiate(_prefab, _parent);
                go.SetActive(false);
                pool.Push(go);
            }
            var poolComponent = EnsurePoolComponent(_parent);
            poolComponent.Prewarm(pool);
        }

        private static ObjectPoolComponent EnsurePoolComponent(Transform parent)
        {
            if (parent == null)
            {
                var go = new GameObject("FactoryPool");
                Object.DontDestroyOnLoad(go);
                parent = go.transform;
            }
            var component = parent.GetComponent<ObjectPoolComponent>();
            if (component == null)
                component = parent.gameObject.AddComponent<ObjectPoolComponent>();
            return component;
        }
    }

    public class ObjectPoolComponent : MonoBehaviour
    {
        private readonly System.Collections.Generic.Stack<GameObject> _pool = new();

        public void Prewarm(System.Collections.Generic.Stack<GameObject> items)
        {
            while (items.Count > 0)
                _pool.Push(items.Pop());
        }

        public GameObject Get(GameObject prefab, Transform parent = null)
        {
            if (_pool.TryPop(out var obj))
            {
                obj.transform.SetParent(parent);
                obj.SetActive(true);
                return obj;
            }
            return Object.Instantiate(prefab, parent);
        }

        public void Return(GameObject obj)
        {
            obj.SetActive(false);
            _pool.Push(obj);
        }
    }
}
```

#### 4. 命令系统 (Command Pattern)

```csharp
// Assets/Scripts/Core/Commands/ICommand.cs
using UnityEngine;

namespace GameFramework.Core.Commands
{
    public interface ICommand
    {
        void Execute();
        void Undo();
        string Description { get; }
    }

    [System.Serializable]
    public struct MoveCommandData
    {
        public Transform target;
        public Vector3 from;
        public Vector3 to;
        public float duration;
    }

    public class MoveCommand : ICommand
    {
        private readonly MoveCommandData _data;
        private float _elapsed;

        public string Description => $"Move {_data.target.name}";

        public MoveCommand(MoveCommandData data) => _data = data;

        public void Execute()
        {
            if (_data.target != null)
                _data.target.position = _data.to;
        }

        public void Undo()
        {
            if (_data.target != null)
                _data.target.position = _data.from;
        }
    }

    public class SpawnCommand : ICommand
    {
        private readonly GameObject _prefab;
        private readonly Vector3 _position;
        private GameObject _spawned;
        private bool _executed;

        public string Description => $"Spawn {_prefab.name}";

        public SpawnCommand(GameObject prefab, Vector3 position)
        {
            _prefab = prefab;
            _position = position;
        }

        public void Execute()
        {
            if (_executed) return;
            _spawned = Object.Instantiate(_prefab, _position, Quaternion.identity);
            _executed = true;
        }

        public void Undo()
        {
            if (!_executed || _spawned == null) return;
            Object.Destroy(_spawned);
            _executed = false;
        }
    }

    public class CommandInvoker : MonoBehaviour
    {
        [SerializeField] private int _maxHistory = 50;
        private readonly System.Collections.Generic.Stack<ICommand> _history = new();

        public void Execute(ICommand command)
        {
            command.Execute();
            _history.Push(command);
            TrimHistory();
        }

        public void Undo()
        {
            if (_history.Count == 0) return;
            var command = _history.Pop();
            command.Undo();
        }

        public bool CanUndo => _history.Count > 0;
        public int HistoryCount => _history.Count;

        private void TrimHistory()
        {
            while (_history.Count > _maxHistory)
            {
                var array = _history.ToArray();
                _history.Clear();
                for (int i = array.Length - 2; i >= 0; i--)
                    _history.Push(array[i]);
            }
        }
    }
}
```
