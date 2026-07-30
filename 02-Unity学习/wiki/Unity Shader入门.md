---
created: 2026-07-30
tags: [Unity, Shader, 图形学]
aliases: [Shader, HLSL, CG]
---

# Unity Shader 入门到精通

## 核心概念

### 渲染管线
1. **应用阶段** — CPU 准备数据（模型、纹理、光源）
2. **几何阶段** — 顶点着色器处理顶点变换
3. **光栅化阶段** — 片元着色器计算每个像素颜色
4. **输出合并** — 深度测试、模板测试、颜色混合

### Shader 类型
| 类型 | 特点 | 适用场景 |
|------|------|----------|
| 顶点/片元 Shader | 最灵活，手动控制每个顶点/像素 | 自定义效果 |
| 表面 Shader | Unity 封装，自动处理光照 | 快速实现材质 |
| Shader Graph | 可视化节点编辑 | 美术人员使用 |

### ShaderLab 基本结构
```csharp
Shader "Custom/MyShader"
{
    Properties { /* 材质面板参数 */ }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            // 顶点着色器
            // 片元着色器
            ENDCG
        }
    }
}
```

## 生产级代码

### 1. 基础顶点/片元着色器

```hlsl
Shader "GameFramework/Diffuse"
{
    Properties
    {
        _MainTex ("纹理", 2D) = "white" {}
        _Color ("颜色", Color) = (1,1,1,1)
        _Gloss ("光泽度", Range(8,256)) = 32
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 200

        Pass
        {
            Tags { "LightMode"="ForwardBase" }

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fwdbase
            #pragma target 3.0

            #include "UnityCG.cginc"
            #include "Lighting.cginc"
            #include "AutoLight.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                float3 worldPos : TEXCOORD2;
                SHADOW_COORDS(3)
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            float _Gloss;

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                TRANSFER_SHADOW(o);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 texColor = tex2D(_MainTex, i.uv) * _Color;

                float3 N = normalize(i.worldNormal);
                float3 L = normalize(_WorldSpaceLightPos0.xyz);
                float3 V = normalize(_WorldSpaceCameraPos.xyz - i.worldPos);
                float3 H = normalize(L + V);

                // 漫反射 (Lambert)
                float diff = max(0, dot(N, L));
                fixed3 diffuse = diff * _LightColor0.rgb * texColor.rgb;

                // 高光 (Blinn-Phong)
                float spec = pow(max(0, dot(N, H)), _Gloss);
                fixed3 specular = spec * _LightColor0.rgb * 0.5;

                // 环境光
                fixed3 ambient = UNITY_LIGHTMODEL_AMBIENT.rgb * texColor.rgb;

                // 阴影
                float shadow = SHADOW_ATTENUATION(i);
                fixed3 final = ambient + (diffuse + specular) * shadow;

                return fixed4(final, texColor.a);
            }
            ENDCG
        }

        // 阴影投射 Pass
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_shadowcaster
            #include "UnityCG.cginc"
            struct v2f { V2F_SHADOW_CASTER; };
            v2f vert(appdata_base v) { v2f o; TRANSFER_SHADOW_CASTER_NORMALOFFSET(o); return o; }
            float4 frag(v2f i) : SV_Target { SHADOW_CASTER_FRAGMENT(i); }
            ENDCG
        }
    }
    FallBack "Diffuse"
}
```

### 2. 透明/混合 Shader

```hlsl
Shader "GameFramework/Transparent"
{
    Properties
    {
        _MainTex ("纹理", 2D) = "white" {}
        _Color ("颜色", Color) = (1,1,1,1)
        _Cutoff ("透明裁剪阈值", Range(0,1)) = 0.5
        [Toggle] _UseCutout ("启用裁剪", Float) = 0
    }

    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "IgnoreProjector"="True" }
        LOD 200

        Pass
        {
            ZWrite Off
            Blend SrcAlpha OneMinusSrcAlpha

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma shader_feature _USECUTOUT_ON
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            fixed _Cutoff;

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv) * _Color;
                #if _USECUTOUT_ON
                    clip(col.a - _Cutoff);
                #endif
                return col;
            }
            ENDCG
        }
    }
    FallBack "Transparent/VertexLit"
}
```

### 3. 法线贴图 Shader

```hlsl
Shader "GameFramework/NormalMap"
{
    Properties
    {
        _MainTex ("主纹理", 2D) = "white" {}
        _BumpMap ("法线贴图", 2D) = "bump" {}
        _BumpScale ("法线强度", Range(0,2)) = 1
        _Color ("颜色", Color) = (1,1,1,1)
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }

        Pass
        {
            Tags { "LightMode"="ForwardBase" }
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "Lighting.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float4 tangent : TANGENT;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 tspace0 : TEXCOORD1;
                float3 tspace1 : TEXCOORD2;
                float3 tspace2 : TEXCOORD3;
                float3 worldPos : TEXCOORD4;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            sampler2D _BumpMap;
            float4 _BumpMap_ST;
            float _BumpScale;
            fixed4 _Color;

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;

                float3 worldNormal = UnityObjectToWorldNormal(v.normal);
                float3 worldTangent = UnityObjectToWorldDir(v.tangent.xyz);
                float3 worldBinormal = cross(worldNormal, worldTangent) * v.tangent.w;

                o.tspace0 = float3(worldTangent.x, worldBinormal.x, worldNormal.x);
                o.tspace1 = float3(worldTangent.y, worldBinormal.y, worldNormal.y);
                o.tspace2 = float3(worldTangent.z, worldBinormal.z, worldNormal.z);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 texColor = tex2D(_MainTex, i.uv) * _Color;

                // 采样法线贴图，从切线空间转换到世界空间
                float3 bump = UnpackNormal(tex2D(_BumpMap, i.uv));
                bump.xy *= _BumpScale;
                bump.z = sqrt(1 - saturate(dot(bump.xy, bump.xy)));

                float3 N = normalize(float3(
                    dot(i.tspace0, bump),
                    dot(i.tspace1, bump),
                    dot(i.tspace2, bump)
                ));

                float3 L = normalize(_WorldSpaceLightPos0.xyz);
                float3 V = normalize(_WorldSpaceCameraPos.xyz - i.worldPos);
                float3 H = normalize(L + V);

                float diff = max(0, dot(N, L));
                float spec = pow(max(0, dot(N, H)), 32);

                fixed3 lighting = (diff + spec * 0.3) * _LightColor0.rgb;
                fixed3 ambient = UNITY_LIGHTMODEL_AMBIENT.rgb * 0.3;
                return fixed4(texColor.rgb * (ambient + lighting), texColor.a);
            }
            ENDCG
        }
    }
    FallBack "Diffuse"
}
```

### 4. Shader Graph 封装（URP）

```hlsl
// 基于 URP 的自定义 Lit Shader
Shader "GameFramework/URP/Lit"
{
    Properties
    {
        [MainTexture] _BaseMap ("基础贴图", 2D) = "white" {}
        [MainColor] _BaseColor ("基础颜色", Color) = (1,1,1,1)
        _Metallic ("金属度", Range(0,1)) = 0
        _Smoothness ("光滑度", Range(0,1)) = 0.5
        _NormalMap ("法线贴图", 2D) = "bump" {}
        _OcclusionMap ("AO贴图", 2D) = "white" {}
        _EmissionMap ("自发光贴图", 2D) = "black" {}
        _EmissionColor ("自发光颜色", Color) = (0,0,0,0)
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        LOD 300

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _Metallic;
            half _Smoothness;
            half4 _EmissionColor;
        CBUFFER_END

        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
        TEXTURE2D(_OcclusionMap); SAMPLER(sampler_OcclusionMap);
        TEXTURE2D(_EmissionMap); SAMPLER(sampler_EmissionMap);

        struct Attributes
        {
            float4 positionOS : POSITION;
            float3 normalOS : NORMAL;
            float4 tangentOS : TANGENT;
            float2 uv : TEXCOORD0;
        };

        struct Varyings
        {
            float4 positionCS : SV_POSITION;
            float2 uv : TEXCOORD0;
            float3 positionWS : TEXCOORD1;
            half3 normalWS : TEXCOORD2;
            half4 tangentWS : TEXCOORD3;
            half3 bitangentWS : TEXCOORD4;
        };
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS
            #pragma multi_compile _ _SHADOWS_SOFT
            #pragma target 3.0

            Varyings vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                output.positionWS = TransformObjectToWorld(input.positionOS.xyz);
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.tangentWS = float4(TransformObjectToWorldDir(input.tangentOS.xyz), input.tangentOS.w);
                output.bitangentWS = cross(output.normalWS, output.tangentWS.xyz) * input.tangentOS.w;
                return output;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half4 baseMap = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv) * _BaseColor;

                half3 normalTS = UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, i.uv));
                half3 normalWS = normalize(
                    normalTS.x * i.tangentWS.xyz +
                    normalTS.y * i.bitangentWS +
                    normalTS.z * i.normalWS
                );

                half occlusion = SAMPLE_TEXTURE2D(_OcclusionMap, sampler_OcclusionMap, i.uv).r;
                half4 emission = SAMPLE_TEXTURE2D(_EmissionMap, sampler_EmissionMap, i.uv) * _EmissionColor;

                #ifdef _MAIN_LIGHT_SHADOWS
                    float4 shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                    half shadow = MainLightShadow(shadowCoord);
                #else
                    half shadow = 1;
                #endif

                Light mainLight = GetMainLight(shadow);
                half3 diffuse = LightingLambert(mainLight.color, mainLight.direction, normalWS);
                half3 specular = LightingSpecular(
                    mainLight.color, mainLight.direction,
                    normalize(_WorldSpaceCameraPos.xyz - i.positionWS),
                    normalWS, half4(1,1,1,1), _Smoothness
                );

                half3 finalColor = baseMap.rgb * (diffuse + mainLight.color * 0.05) + specular + emission.rgb;
                return half4(finalColor, baseMap.a);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            HLSLPROGRAM
            #pragma vertex ShadowPassVertex
            #pragma fragment ShadowPassFragment
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            struct ShadowAttributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct ShadowVaryings { float4 positionCS : SV_POSITION; };
            ShadowVaryings ShadowPassVertex(ShadowAttributes input)
            {
                ShadowVaryings o;
                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.positionCS = TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, _LightDirection));
                return o;
            }
            half4 ShadowPassFragment(ShadowVaryings i) : SV_Target { return 0; }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
```

## 相关链接
- [[Unity动画系统]]
- [[Unity 性能优化]]

## 来源
- 原始资料：[[raw/2026-07-30-麦扣UnityShader课程]]
