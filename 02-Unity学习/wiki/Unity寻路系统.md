---
created: 2026-07-30
tags: [Unity, 寻路, AI]
aliases: [Navigation, NavMesh]
---

# Unity 寻路系统（Navigation）

## 核心概念

基于 **NavMesh（导航网格）** 的自动寻路系统。

### 工作流程
1. **烘焙 NavMesh**: Window → AI → Navigation → Bake
2. **挂载 NavMeshAgent**: 角色添加 NavMeshAgent 组件
3. **设置目标**: `agent.SetDestination(targetPosition)`
4. **自动寻路**: Agent 自动计算路径

### 关键组件

| 组件 | 作用 |
|------|------|
| NavMesh | 烘焙出的可行走区域 |
| NavMeshAgent | 角色移动控制 |
| NavMeshObstacle | 动态障碍物 |
| OffMeshLink | 跳跃/梯子特殊路径 |

## 生产级代码

### 1. AI 导航控制器（巡逻/追击/逃跑）

```csharp
using UnityEngine;
using UnityEngine.AI;

namespace GameFramework.AI
{
    public enum AIState
    {
        Idle,
        Patrol,
        Chase,
        Flee,
        ReturnToSpawn
    }

    [RequireComponent(typeof(NavMeshAgent))]
    public sealed class AINavigationController : MonoBehaviour
    {
        [Header("Movement")]
        [SerializeField] private float _walkSpeed = 3.5f;
        [SerializeField] private float _runSpeed = 7f;
        [SerializeField] private float _angularSpeed = 360f;
        [SerializeField] private float _stoppingDistance = 1.5f;

        [Header("Patrol")]
        [SerializeField] private Transform[] _patrolPoints;
        [SerializeField] private float _waitTimeAtPoint = 2f;
        [SerializeField] private bool _randomPatrol = true;

        [Header("Detection")]
        [SerializeField] private float _detectionRange = 15f;
        [SerializeField] private float _fleeRange = 8f;
        [SerializeField] private LayerMask _targetLayer = 1;

        [Header("Return")]
        [SerializeField] private float _returnThreshold = 25f;

        private NavMeshAgent _agent;
        private AIState _currentState;
        private Transform _target;
        private Vector3 _spawnPosition;
        private int _currentPatrolIndex;
        private float _stateTimer;
        private float _waitTimer;

        public AIState CurrentState => _currentState;
        public event System.Action<AIState> OnStateChanged;

        private void Awake()
        {
            _agent = GetComponent<NavMeshAgent>();
            _spawnPosition = transform.position;
        }

        private void Start()
        {
            TransitionTo(AIState.Patrol);
        }

        private void Update()
        {
            _stateTimer += Time.deltaTime;

            switch (_currentState)
            {
                case AIState.Idle: UpdateIdle(); break;
                case AIState.Patrol: UpdatePatrol(); break;
                case AIState.Chase: UpdateChase(); break;
                case AIState.Flee: UpdateFlee(); break;
                case AIState.ReturnToSpawn: UpdateReturn(); break;
            }

            EvaluateStateTransitions();
        }

        private void EvaluateStateTransitions()
        {
            var detected = FindNearestTarget();

            if (detected != null && !IsInState(AIState.Flee))
            {
                var dist = Vector3.Distance(transform.position, detected.position);

                if (dist <= _fleeRange && _currentState == AIState.Chase)
                {
                    TransitionTo(AIState.Flee);
                    return;
                }

                if (dist <= _detectionRange && _currentState != AIState.Chase)
                {
                    _target = detected;
                    TransitionTo(AIState.Chase);
                    return;
                }
            }

            if (_currentState == AIState.Chase && _target == null)
            {
                TransitionTo(AIState.Patrol);
            }

            if (_currentState == AIState.Flee && _stateTimer > 5f)
            {
                TransitionTo(AIState.Patrol);
            }

            if (_currentState != AIState.ReturnToSpawn &&
                Vector3.Distance(transform.position, _spawnPosition) > _returnThreshold)
            {
                TransitionTo(AIState.ReturnToSpawn);
            }
        }

        private void UpdateIdle()
        {
            if (_stateTimer >= _waitTimeAtPoint)
                TransitionTo(AIState.Patrol);
        }

        private void UpdatePatrol()
        {
            if (!_agent.pathPending && _agent.remainingDistance <= _agent.stoppingDistance)
            {
                _waitTimer += Time.deltaTime;
                if (_waitTimer >= _waitTimeAtPoint)
                {
                    _waitTimer = 0;
                    MoveToNextPatrolPoint();
                }
            }
        }

        private void UpdateChase()
        {
            if (_target == null) return;

            _agent.SetDestination(_target.position);

            var speed = _agent.remainingDistance > _detectionRange * 0.5f
                ? _runSpeed : _walkSpeed;
            _agent.speed = Mathf.Lerp(_agent.speed, speed, Time.deltaTime * 2f);
        }

        private void UpdateFlee()
        {
            if (_target == null) return;

            var fleeDir = (transform.position - _target.position).normalized;
            var fleePos = transform.position + fleeDir * _fleeRange * 2f;

            if (NavMesh.SamplePosition(fleePos, out var hit, 5f, NavMesh.AllAreas))
                _agent.SetDestination(hit.position);
        }

        private void UpdateReturn()
        {
            _agent.speed = _runSpeed;
            _agent.SetDestination(_spawnPosition);

            if (!_agent.pathPending && _agent.remainingDistance <= _agent.stoppingDistance)
                TransitionTo(AIState.Patrol);
        }

        private Transform FindNearestTarget()
        {
            var colliders = Physics.OverlapSphere(transform.position, _detectionRange, _targetLayer);
            Transform nearest = null;
            var minDist = float.MaxValue;

            foreach (var col in colliders)
            {
                var dist = Vector3.Distance(transform.position, col.transform.position);
                if (dist < minDist)
                {
                    minDist = dist;
                    nearest = col.transform;
                }
            }
            return nearest;
        }

        private void MoveToNextPatrolPoint()
        {
            if (_patrolPoints == null || _patrolPoints.Length == 0) return;

            if (_randomPatrol)
                _currentPatrolIndex = Random.Range(0, _patrolPoints.Length);
            else
                _currentPatrolIndex = (_currentPatrolIndex + 1) % _patrolPoints.Length;

            var point = _patrolPoints[_currentPatrolIndex];
            if (point != null)
                _agent.SetDestination(point.position);
        }

        private void TransitionTo(AIState newState)
        {
            var prev = _currentState;
            _currentState = newState;
            _stateTimer = 0f;
            _waitTimer = 0f;
            OnStateChanged?.Invoke(newState);
            ConfigureState(newState);
        }

        private void ConfigureState(AIState state)
        {
            switch (state)
            {
                case AIState.Idle:
                    _agent.isStopped = true;
                    _agent.speed = 0;
                    break;

                case AIState.Patrol:
                    _agent.isStopped = false;
                    _agent.speed = _walkSpeed;
                    MoveToNextPatrolPoint();
                    break;

                case AIState.Chase:
                    _agent.isStopped = false;
                    _agent.speed = _runSpeed;
                    _agent.stoppingDistance = _stoppingDistance;
                    break;

                case AIState.Flee:
                    _agent.isStopped = false;
                    _agent.speed = _runSpeed;
                    _agent.stoppingDistance = 1f;
                    break;

                case AIState.ReturnToSpawn:
                    _agent.isStopped = false;
                    _agent.speed = _runSpeed;
                    _agent.stoppingDistance = 1f;
                    break;
            }
        }

        public void SetTarget(Transform target)
        {
            _target = target;
        }

        public void ForceState(AIState state)
        {
            TransitionTo(state);
        }

        public bool IsInState(AIState state)
        {
            return _currentState == state;
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, _detectionRange);
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(transform.position, _fleeRange);
        }
    }
}
```

### 2. 寻路代理封装器

```csharp
using UnityEngine;
using UnityEngine.AI;

namespace GameFramework.AI
{
    [RequireComponent(typeof(NavMeshAgent))]
    public sealed class NavMeshAgentWrapper : MonoBehaviour
    {
        private NavMeshAgent _agent;

        [SerializeField] private float _baseSpeed = 5f;
        [SerializeField] private float _acceleration = 8f;
        [SerializeField] private float _turnSpeed = 360f;

        public float RemainingDistance => _agent.remainingDistance;
        public bool IsPathPending => _agent.pathPending;
        public bool HasReachedDestination =>
            !_agent.pathPending && _agent.remainingDistance <= _agent.stoppingDistance;
        public bool IsPathValid => _agent.hasPath && _agent.pathStatus == NavMeshPathStatus.PathComplete;

        private void Awake()
        {
            _agent = GetComponent<NavMeshAgent>();
            ConfigureAgent();
        }

        private void ConfigureAgent()
        {
            _agent.speed = _baseSpeed;
            _agent.acceleration = _acceleration;
            _agent.angularSpeed = _turnSpeed;
            _agent.autoBraking = true;
            _agent.autoRepath = true;
        }

        public bool MoveTo(Vector3 destination)
        {
            return _agent.SetDestination(destination);
        }

        public bool MoveTo(Vector3 destination, float speedMultiplier)
        {
            _agent.speed = _baseSpeed * Mathf.Clamp01(speedMultiplier);
            return _agent.SetDestination(destination);
        }

        public void Stop()
        {
            _agent.isStopped = true;
            _agent.velocity = Vector3.zero;
        }

        public void Resume()
        {
            _agent.isStopped = false;
        }

        public void WarpTo(Vector3 position)
        {
            _agent.Warp(position);
        }

        public bool SamplePosition(Vector3 source, out Vector3 result, float maxDistance)
        {
            if (NavMesh.SamplePosition(source, out var hit, maxDistance, NavMesh.AllAreas))
            {
                result = hit.position;
                return true;
            }
            result = source;
            return false;
        }

        public float CalculatePathLength(Vector3 destination)
        {
            var path = new NavMeshPath();
            if (_agent.CalculatePath(destination, path) && path.status == NavMeshPathStatus.PathComplete)
            {
                var length = 0f;
                for (int i = 1; i < path.corners.Length; i++)
                    length += Vector3.Distance(path.corners[i - 1], path.corners[i]);
                return length;
            }
            return float.MaxValue;
        }

        public void SetSpeed(float speed)
        {
            _agent.speed = Mathf.Max(0f, speed);
        }

        public void SetStoppingDistance(float distance)
        {
            _agent.stoppingDistance = Mathf.Max(0f, distance);
        }
    }
}
```

### 3. 动态障碍物控制器

```csharp
using UnityEngine;
using UnityEngine.AI;

namespace GameFramework.AI
{
    [RequireComponent(typeof(NavMeshObstacle))]
    public sealed class DynamicObstacle : MonoBehaviour
    {
        [SerializeField] private bool _activateOnStart = true;
        [SerializeField] private float _activationRadius = 5f;
        [SerializeField] private LayerMask _playerLayer = 1;

        private NavMeshObstacle _obstacle;
        private bool _isActive;
        private Transform _player;

        private void Awake()
        {
            _obstacle = GetComponent<NavMeshObstacle>();
            _obstacle.carving = true;
        }

        private void Start()
        {
            SetActive(_activateOnStart);
        }

        private void Update()
        {
            if (_player == null)
            {
                FindPlayer();
                return;
            }

            var dist = Vector3.Distance(transform.position, _player.position);
            SetActive(dist <= _activationRadius);
        }

        private void FindPlayer()
        {
            var col = Physics.OverlapSphere(transform.position, _activationRadius * 2f, _playerLayer);
            if (col.Length > 0)
                _player = col[0].transform;
        }

        public void SetActive(bool active)
        {
            if (_isActive == active) return;
            _isActive = active;
            _obstacle.enabled = active;
            _obstacle.carving = active;
        }

        public void Toggle()
        {
            SetActive(!_isActive);
        }

        private void OnDestroy()
        {
            if (_obstacle != null)
            {
                _obstacle.carving = false;
                _obstacle.enabled = false;
            }
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1, 0.5f, 0, 0.3f);
            Gizmos.DrawWireSphere(transform.position, _activationRadius);
        }
    }
}
```

### 4. 路径可视化调试器

```csharp
using UnityEngine;
using UnityEngine.AI;

namespace GameFramework.AI
{
    [RequireComponent(typeof(NavMeshAgent))]
    public sealed class PathVisualizer : MonoBehaviour
    {
        [SerializeField] private bool _showPath = true;
        [SerializeField] private Color _pathColor = Color.cyan;
        [SerializeField] private Color _waypointColor = Color.yellow;
        [SerializeField] private float _waypointSize = 0.3f;

        private NavMeshAgent _agent;
        private NavMeshPath _debugPath;

        private void Awake()
        {
            _agent = GetComponent<NavMeshAgent>();
        }

        private void Update()
        {
            if (_agent.hasPath && _agent.path != null)
                _debugPath = _agent.path;
        }

        private void OnDrawGizmos()
        {
            if (!_showPath || _debugPath == null) return;

            for (int i = 0; i < _debugPath.corners.Length - 1; i++)
            {
                Debug.DrawLine(_debugPath.corners[i], _debugPath.corners[i + 1], _pathColor);
                Gizmos.color = _waypointColor;
                Gizmos.DrawSphere(_debugPath.corners[i], _waypointSize);
            }

            if (_debugPath.corners.Length > 0)
            {
                Gizmos.color = Color.green;
                Gizmos.DrawSphere(_debugPath.corners[_debugPath.corners.Length - 1], _waypointSize * 1.5f);
            }
        }
    }
}
```

## 相关链接
- [[Unity动画系统]]

## 来源
- 原始资料：[[raw/2026-07-30-麦扣Unity动画系统课程]]
