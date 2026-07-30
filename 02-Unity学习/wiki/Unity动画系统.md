---
created: 2026-07-30
tags: [Unity, 动画]
aliases: [Animation, Animator]
---

# Unity 动画系统

## 核心概念

**Animator Controller** 是 Unity 动画系统的核心，通过**状态机**管理动画切换。

### 关键组件

| 组件 | 作用 |
|------|------|
| Animation Clip | 单个动画片段（记录属性变化曲线） |
| Animator Controller | 状态机容器，定义状态和转换 |
| Avatar | 角色骨骼映射（人形/泛型） |
| Animator | 挂载在 GameObject 上的执行组件 |

### 模型导入设置

- **Rig 选项卡**: Humanoid（支持重定向）/ Generic / Legacy
- **Animation 选项卡**: 拆分 Clip、设置循环、压缩

### 工作流

1. 导入模型，Rig 选项卡选择 Humanoid/Generic
2. Animation 选项卡拆分 Clip、设置循环
3. 创建 Animator Controller，添加状态
4. 设置参数驱动状态转换
5. 代码控制播放
6. Blend Tree 平滑混合
7. Layer 分层控制不同身体部位

## 生产级代码

### 1. 动画管理器（完整状态控制）

```csharp
using UnityEngine;
using System;

namespace GameFramework.Animation
{
    public sealed class AnimationController : MonoBehaviour
    {
        [SerializeField] private Animator _animator;
        [SerializeField] private float _crossFadeDuration = 0.1f;

        private readonly int _speedHash = Animator.StringToHash("Speed");
        private readonly int _directionHash = Animator.StringToHash("Direction");
        private readonly int _triggerAttackHash = Animator.StringToHash("Attack");
        private readonly int _triggerHitHash = Animator.StringToHash("Hit");
        private readonly int _triggerDeathHash = Animator.StringToHash("Death");
        private readonly int _stateHash = Animator.StringToHash("State");
        private readonly int _isMovingHash = Animator.StringToHash("IsMoving");
        private readonly int _isGroundedHash = Animator.StringToHash("IsGrounded");

        private void Awake()
        {
            if (_animator == null)
                _animator = GetComponent<Animator>();
        }

        public void SetMovement(float speed, float direction)
        {
            _animator.SetFloat(_speedHash, speed, 0.1f, Time.deltaTime);
            _animator.SetFloat(_directionHash, direction, 0.1f, Time.deltaTime);
            _animator.SetBool(_isMovingHash, speed > 0.1f);
        }

        public void SetGrounded(bool grounded)
        {
            _animator.SetBool(_isGroundedHash, grounded);
        }

        public void SetState(int state)
        {
            _animator.SetInteger(_stateHash, state);
        }

        public void PlayAttack()
        {
            _animator.SetTrigger(_triggerAttackHash);
        }

        public void PlayHit()
        {
            _animator.SetTrigger(_triggerHitHash);
        }

        public void PlayDeath()
        {
            _animator.SetTrigger(_triggerDeathHash);
            _animator.SetInteger(_stateHash, -1);
        }

        public void CrossFade(string stateName)
        {
            _animator.CrossFade(stateName, _crossFadeDuration);
        }

        public AnimatorStateInfo GetCurrentState(int layer = 0)
        {
            return _animator.GetCurrentAnimatorStateInfo(layer);
        }

        public bool IsPlaying(string stateName, int layer = 0)
        {
            var state = _animator.GetCurrentAnimatorStateInfo(layer);
            return state.IsName(stateName) && state.normalizedTime < 1f;
        }

        public float GetNormalizedTime(int layer = 0)
        {
            return _animator.GetCurrentAnimatorStateInfo(layer).normalizedTime;
        }

        public void SetLayerWeight(int layer, float weight)
        {
            _animator.SetLayerWeight(layer, Mathf.Clamp01(weight));
        }

        public void ResetTriggers()
        {
            _animator.ResetTrigger(_triggerAttackHash);
            _animator.ResetTrigger(_triggerHitHash);
            _animator.ResetTrigger(_triggerDeathHash);
        }
    }
}
```

### 2. 状态机基类（可复用架构）

```csharp
using System;
using UnityEngine;

namespace GameFramework.FSM
{
    public abstract class StateMachineBehaviour : MonoBehaviour
    {
        private IState _currentState;
        private IState _previousState;

        protected void TransitionTo(IState nextState)
        {
            _currentState?.Exit();
            _previousState = _currentState;
            _currentState = nextState;
            _currentState.Enter();
        }

        protected void TransitionTo<T>() where T : IState
        {
            // 按需通过依赖注入或工厂创建
        }

        public bool IsInState<T>() where T : IState
        {
            return _currentState is T;
        }

        private void Update()
        {
            _currentState?.Tick(Time.deltaTime);
        }

        private void FixedUpdate()
        {
            _currentState?.FixedTick(Time.fixedDeltaTime);
        }

        private void LateUpdate()
        {
            _currentState?.LateTick(Time.deltaTime);
        }
    }

    public interface IState
    {
        void Enter();
        void Tick(float delta);
        void FixedTick(float delta);
        void LateTick(float delta);
        void Exit();
    }
}
```

### 3. 角色战斗状态机示例

```csharp
using UnityEngine;
using GameFramework.Animation;

namespace GameFramework.FSM.Character
{
    public class CharacterStateMachine : StateMachineBehaviour
    {
        [SerializeField] private AnimationController _anim;

        private IdleState _idle;
        private MoveState _move;
        private AttackState _attack;
        private HitState _hit;
        private DeathState _death;

        private void Start()
        {
            _idle = new IdleState(_anim);
            _move = new MoveState(_anim);
            _attack = new AttackState(_anim);
            _hit = new HitState(_anim);
            _death = new DeathState(_anim);

            TransitionTo(_idle);
        }

        public void OnMoveInput(float speed, float direction)
        {
            if (IsInState<IdleState>() || IsInState<MoveState>())
            {
                if (speed > 0.1f)
                    TransitionTo(_move);
                else
                    TransitionTo(_idle);
            }
            _anim.SetMovement(speed, direction);
        }

        public void OnAttackInput()
        {
            if (IsInState<IdleState>() || IsInState<MoveState>())
                TransitionTo(_attack);
        }

        public void OnTakeDamage()
        {
            if (!IsInState<DeathState>())
                TransitionTo(_hit);
        }

        public void OnDeath()
        {
            TransitionTo(_death);
        }
    }

    public class IdleState : IState
    {
        private readonly AnimationController _anim;
        public IdleState(AnimationController anim) => _anim = anim;
        public void Enter() => _anim.SetState(0);
        public void Tick(float delta) {}
        public void FixedTick(float delta) {}
        public void LateTick(float delta) {}
        public void Exit() {}
    }

    public class MoveState : IState
    {
        private readonly AnimationController _anim;
        public MoveState(AnimationController anim) => _anim = anim;
        public void Enter() => _anim.SetState(1);
        public void Tick(float delta) {}
        public void FixedTick(float delta) {}
        public void LateTick(float delta) {}
        public void Exit() {}
    }

    public class AttackState : IState
    {
        private readonly AnimationController _anim;
        private float _timer;
        public AttackState(AnimationController anim) => _anim = anim;
        public void Enter()
        {
            _timer = 0f;
            _anim.PlayAttack();
        }
        public void Tick(float delta) => _timer += delta;
        public void FixedTick(float delta) {}
        public void LateTick(float delta) {}
        public void Exit() => _anim.ResetTriggers();
    }

    public class HitState : IState
    {
        private readonly AnimationController _anim;
        private float _timer;
        public HitState(AnimationController anim) => _anim = anim;
        public void Enter()
        {
            _timer = 0f;
            _anim.PlayHit();
        }
        public void Tick(float delta) => _timer += delta;
        public void FixedTick(float delta) {}
        public void LateTick(float delta) {}
        public void Exit() => _anim.ResetTriggers();
    }

    public class DeathState : IState
    {
        private readonly AnimationController _anim;
        public DeathState(AnimationController anim) => _anim = anim;
        public void Enter() => _anim.PlayDeath();
        public void Tick(float delta) {}
        public void FixedTick(float delta) {}
        public void LateTick(float delta) {}
        public void Exit() {}
    }
}
```

### 4. IK 控制器（手脚贴合地形）

```csharp
using UnityEngine;

namespace GameFramework.Animation
{
    public sealed class IKController : MonoBehaviour
    {
        [Header("IK Settings")]
        [SerializeField] private Animator _animator;
        [SerializeField] private bool _enableIK = true;
        [SerializeField] private float _ikWeight = 1f;

        [Header("Foot IK")]
        [SerializeField] private LayerMask _groundLayer = 1;
        [SerializeField] private float _footOffset = 0.05f;
        [SerializeField] private float _raycastDistance = 1.5f;

        [Header("Hand IK")]
        [SerializeField] private Transform _leftHandTarget;
        [SerializeField] private Transform _rightHandTarget;
        [SerializeField] private float _handIKWeight = 0.5f;

        private void Awake()
        {
            if (_animator == null)
                _animator = GetComponent<Animator>();
        }

        private void OnAnimatorIK(int layerIndex)
        {
            if (!_enableIK || _animator == null) return;

            HandleFootIK(AvatarIKGoal.LeftFoot);
            HandleFootIK(AvatarIKGoal.RightFoot);
            HandleHandIK(AvatarIKGoal.LeftHand, _leftHandTarget);
            HandleHandIK(AvatarIKGoal.RightHand, _rightHandTarget);
        }

        private void HandleFootIK(AvatarIKGoal foot)
        {
            var weight = _ikWeight * _animator.GetIKPositionWeight(foot);
            _animator.SetIKPositionWeight(foot, weight);
            _animator.SetIKRotationWeight(foot, weight);

            var origin = _animator.GetIKPosition(foot);
            origin.y += _raycastDistance * 0.5f;

            if (Physics.Raycast(origin, Vector3.down, out var hit, _raycastDistance, _groundLayer))
            {
                var targetPos = hit.point + Vector3.up * _footOffset;
                _animator.SetIKPosition(foot, targetPos);

                var forward = Vector3.ProjectOnPlane(transform.forward, hit.normal);
                var targetRot = Quaternion.LookRotation(forward, hit.normal);
                _animator.SetIKRotation(foot, targetRot);
            }
        }

        private void HandleHandIK(AvatarIKGoal hand, Transform target)
        {
            if (target == null) return;

            _animator.SetIKPositionWeight(hand, _handIKWeight);
            _animator.SetIKRotationWeight(hand, _handIKWeight);
            _animator.SetIKPosition(hand, target.position);
            _animator.SetIKRotation(hand, target.rotation);
        }

        public void SetIKEnable(bool enable)
        {
            _enableIK = enable;
        }

        public void SetHandTargets(Transform left, Transform right)
        {
            _leftHandTarget = left;
            _rightHandTarget = right;
        }
    }
}
```

### 5. Root Motion 控制器

```csharp
using UnityEngine;

namespace GameFramework.Animation
{
    [RequireComponent(typeof(CharacterController))]
    public sealed class RootMotionController : MonoBehaviour
    {
        [SerializeField] private Animator _animator;
        [SerializeField] private float _rotationSpeed = 10f;
        [SerializeField] private float _forwardSpeed = 1f;

        private CharacterController _charController;
        private Vector3 _rootMotionDelta;
        private Vector3 _rootRotationDelta;

        private void Awake()
        {
            _charController = GetComponent<CharacterController>();
            if (_animator == null)
                _animator = GetComponent<Animator>();

            _animator.applyRootMotion = true;
        }

        private void OnAnimatorMove()
        {
            _rootMotionDelta = _animator.deltaPosition;
            _rootRotationDelta = _animator.deltaRotation.eulerAngles;
        }

        private void Update()
        {
            ApplyRootMotion();
        }

        private void ApplyRootMotion()
        {
            var forward = _rootMotionDelta.z * _forwardSpeed * transform.forward;
            var right = _rootMotionDelta.x * _forwardSpeed * transform.right;
            var vertical = _rootMotionDelta.y * Vector3.up;

            _charController.Move(forward + right + vertical);

            transform.Rotate(0, _rootRotationDelta.y * _rotationSpeed, 0);
        }

        public void SetRootMotionMultiplier(float speed)
        {
            _forwardSpeed = Mathf.Max(0f, speed);
        }
    }
}
```

### 6. 动画事件接收器

```csharp
using System;
using UnityEngine;

namespace GameFramework.Animation
{
    public sealed class AnimationEventReceiver : MonoBehaviour
    {
        public event Action<int> OnHitFrame;
        public event Action<int> OnFootstep;
        public event Action OnAttackFinished;
        public event Action OnSkillCast;
        public event Action OnAnimationEnd;

        public void HitFrame(int damageMultiplier)
        {
            OnHitFrame?.Invoke(damageMultiplier);
        }

        public void Footstep(int footIndex)
        {
            OnFootstep?.Invoke(footIndex);
        }

        public void AttackFinished()
        {
            OnAttackFinished?.Invoke();
        }

        public void SkillCast()
        {
            OnSkillCast?.Invoke();
        }

        public void AnimationEnd()
        {
            OnAnimationEnd?.Invoke();
        }

        private void OnDestroy()
        {
            OnHitFrame = null;
            OnFootstep = null;
            OnAttackFinished = null;
            OnSkillCast = null;
            OnAnimationEnd = null;
        }
    }
}
```

## 相关链接
- [[Unity 性能优化]]
- [[Unity 寻路系统]]

## 来源
- 原始资料：[[raw/2026-07-30-Unity中级学习路径]]
- 原始资料：[[raw/2026-07-30-麦扣Unity动画系统课程]]
