# 背景
阅读本文前，建议先熟悉OAuth2.0、OIDC、JWT等概念：

Gemfield：OAuth2.0、OpenID Connect和JWT
​zhuanlan.zhihu.com/p/351693888
在CivilNet组织内部，我们开发和维护了5个独立的web服务产品，另外开发和维护了10个独立的REST API用来对外提供我们的AI能力。然后不知道因为什么原因，我们必须：

- 使用Python来开发web服务；
- 使用KeyCloak来提供身份验证和授权鉴权服务。

现在假设你无条件认同以上两点，那我们继续。我们在整个所有产品的开发和维护中，主要在实践以下两个经典场景：

# 场景一：web服务

CivilNet组织有5个独立的web服务产品，其中3个是由python开发，2个是由java开发。这5个产品都是给集团内部用户使用的。应集团甲方要求，这些产品必须符合如下要求：

- 这5个web产品都需要提供用户注册登录功能；
- 每个产品上的每个用户都有自身的数据（比如账户里的钱、购买的商品、信用分等）；
- 通过KeyCloak以OIDC规范来提供SSO单点登录功能；
- 用户可以通过用户名+密码进行登录；
- 注册以上用户名+密码的时候需要使用手机号进行验证；
- 用户通过手机号+验证码的方式可以修改密码；
- 用户可以通过手机号+验证码直接登录；
- 用户登录后可以操作各种业务，每个用户有自己独立的业务数据；
- 账户体系按照RBAC设计，也就是Role Based Access Control（基于角色的访问控制），包含用户、角色、权限。

RBAC包含：

- 角色是权限的集合。每个角色至少具备一个权限；
- 一个用户有多个角色，每个用户至少扮演一个角色；
- 一个角色有多个用户；由此，用户和角色是多对多的关系。

因此，在上述的web产品中，RBAC要至少实现以下最基本的内容：

- 创建角色;
- 创建权限;
- 创建用户;
- 检查一个用户的角色中是否有相应的权限来做一件事情(API调用)。

# 场景二：REST API调用

CivilNet组织有10个独立的REST API服务，用以对外提供API能力（比如ocr、人脸识别、语音识别、场景理解等）。外部付费用户和CivilNet按照如下的要求来使用这些REST API：

- 每个购买此REST API服务的外部付费用户将会获得CivilNet提供的AppKey和AppSecret；
- 用户使用REST API业务时，需要用AppKey和AppSecret从服务端换取access token；
- 用户在对REST API的调用中只需要使用access token，access token有效期为2个小时，失效后需要refresh；
- REST API的服务端需要在每次调用中对调用者进行身份验证和鉴权；
- 身份验证得以让REST API服务知晓当前是哪个用户在调用，用以身份核查和计费（CivilNet按照调用次数收费）；当身份非法时，拒绝提供服务；当费用耗尽后，拒绝提供服务；
- 鉴权得以让REST API服务知晓当前的用户是否有权限调用本REST API。比如只购买了OCR服务的用户，在调用人脸识别REST API的时候，人脸识别REST API要拒绝提供服务。

# KeyCloak的一些概念
这个小节Gemfield讨论的内容就是：从KeyCloak这个OP或者Authorization Server的视角来看，开发者应该怎么实现上述两个场景。Keycloak借助自身如下的灵活设计：

- 使用精细的authorization policies 和不同的access control机制来保护资源；
- 集中式的Resource、Permission、Policy管理；
- 集中式的PDP（Policy Decision Point，策略决策点）；
- 一组基于REST的authorization services，提供REST安全服务；
- 授权流程且兼容UMA协议；
- 避免重复开发和部署的基础设施。

从而可以提供以下典型用途:

- Attribute-based access control (ABAC) ；
- Role-based access control (RBAC) ；
- User-based access control (UBAC) ；
- Context-based access control (CBAC)；
- Time-based access control；
- Support for custom access control mechanisms (ACMs) through a Policy Provider Service Provider Interface (SPI)。

CivilNet组织选择了使用KeyCloak来实现RBAC。此外，基于KeyCloak进行实践的时候还需要了解如下的KeyCloak上的概念：

- 在Keycloak中，包含realm、client、service、role、user、group、resource、resource server、policy、Policy Provider、scopes、permission、Permission Ticket这些概念；
- KeyCloak的client应用可以作为resource server，client的resources和它们相应的scopes是由一组authorization policies来保护和管理的；
- resource可以是一组endpoints或者一组HTML页面；
- resource的Scopes 代表了一个被保护的resouce上的一组权限，比如可以是view、edit、delete等：
```
X CAN DO Y ON RESOURCE Z
解释：
X 代表users、roles、groups；
Y 代表一个scope，比如write、view等等；
Z 代表一个被保护的资源，比如一个REST API。
```
- 授予或者拒绝对一个resouce的访问，你需要定义Policy、permission、将Policy适用到permission上、关联一个permission到一个scope或者resource；
- permission有Resource-Based和Scope-Based两种，Resource-Based permission可以应用在resource上，Scope-Based permission可以应用在scope或者scope(s) + resource上;
- role是权限的集合；
- user是Application上的一个或多个用户；
- group是role的集合。

在KeyCloak上将permissions、resource关联的过程中，你可以有多种灵活的方式，比如：

- 定义单独的policies，然后将每个policy绑定到一个permission；
- 定义单独的policies，然后组合成aggregated policy，然后将aggregated policy绑定到scope-based的permission；然后你可以将该scoped-based permission应用到resource以及其相关联的所有scope上；
- 你可以通过resource-based permission的方式来仅仅为resources创建permissions, 然后另外再通过scope-based permission type来将permissions仅仅和scope关联。
 
最后，KeyCloak提供了两种经典的使用流程：

# 典型的OIDC

- CivilNet web应用（RP）请求Keycloak（OP） 帮忙来对一个终端用户（EU）进行身份验证；
- Keycloak（OP）对终端用户（EU）进行身份认证，然后终端用户（EU）授权CivilNet web应用（RP）；
- Keycloak（OP）返回ID Token和Access Token给CivilNet web应用（RP）；其中ID token包含了用户的身份信息，如username、email等，还记得KeyCloak中很有意思的mapper功能吧；而Access Token是被KeyCloak的realm签名的，并且包含了access information（比如role mappings），可以确定终端用户（EU）在CivilNet web应用（RP）上被允许访问的资源；
- CivilNet web应用（RP）携带Access Token发送请求到Keycloak（OP）的UserInfo EndPoint；
- UserInfo EndPoint返回终端用户（EU）的Claims。

典型的OAuth2.0

- Client（CivilNet的web产品）想要访问Resource Server（一个远端rest服务）；
- Client（CivilNet的web产品）请求Authorization Server（KeyCloak）授予一个access token，然后Client（CivilNet的web产品）可以携带此access token并且得以代表Resource Owner（终端用户）访问Resource Server（一个远端rest服务）；
- Authorization Server（KeyCloak）对Resource Owner（终端用户）进行身份验证，然后询问Resource Owner（终端用户）是否授权给Client（CivilNet的web产品）；
- 如果获得Resource Owner（终端用户）授权，Client（CivilNet的web产品）获得access token，这个access token是被KeyCloak realm签名过的。然后Client（CivilNet的web产品）向Resource Server（一个远端rest服务）发起rest api调用，且携带此access token；
- Resource Server（一个远端rest服务）解析此access token，验证签名是否有效，然后依据access token中的access information来决定是否响应该请求。

# 场景一：web服务
我们来看看如何在这个场景下适用上述两个KeyCloak的经典用法。假设我们已经将web12345这5个web产品注册到了KeyCloak中了，如果没有，请按照下述步骤：

## 1，新建realm、user

Keycloak默认有一个master realm，这是用来管理keycloak服务的，用户不应使用master realm来配置自己的应用。所以我们新建一个CivilNet realm：

- 登录Keycloak Admin console；
- Add realm - 新增CivilNet Realm;
- 在CivilNet Realm下 - 新增user: civilnet-gemfield，然后 save;
- 设置上述用户的密码 - Credentials - password - Temporary关闭 - set password;
- Role Mappings - client roles - realm management - 选中所有Available role然后授予上述用户。

## 2，配置user账户

- 访问 http://localhost:8080/auth/realms/gemfield/account
- 用户名：civilnet-gemfield；密码：gemfield；
- 点击Applications - Security Admin Console - Clients - 新建；
- 新建并填写client id: web1 - Client protocol: openid-connect；
- 新建并填写client id: web2 - Client protocol: openid-connect；
- 新建并填写client id: web3 - Client protocol: openid-connect；
- 新建并填写client id: web4 - Client protocol: openid-connect；
- 新建并填写client id: web5 - Client protocol: openid-connect。

然后开始我们的设计：

## step1，role和权限的CURD

web12345服务是基于RBAC的，因此在最基础的层面，我们就要能够进行：

- 角色的CURD;
- 权限的CURD。

我们准备直接通过KeyCloak的dashboard来进行管理。那么，增删改查角色和权限的时候，实际上是在对KeyCloak增删改查什么呢？也就是这个映射关系是怎么建立起来的呢？我们选择了KeyCloak中的resource based permission方案，也就是使用KeyCloak client中的resource(REST API)、permission、policy、role来共同实现角色和权限。

怎么实现呢？CivilNet的开发者们会在文中最后提到的pyRBAC项目里告诉你。

## step2，web12345上的用户注册

按照OIDC规范，用户需要在KeyCloak（OP）上注册有账户，且要有账户的CURD。我们是怎么做的呢？KeyCloak的dashboard只提供了2种主题，远远不能满足企业服务使用。因此这里要开发KeyCloak的主题，包含有企业VI。

KeyCloak允许用户自行注册吗？KeyCloak允许管理员删除用户账户吗？用户注册后，需要对用户进行短信或邮箱验证，这就涉及到发送短信/邮箱验证码的问题了，KeyCloak能搞定短信验证吗？这些不是KeyCloak能搞定的事情，那怎么办呢？只能是加一层wrapper：CivilNet-Account服务。验证成功后，CivilNet-Account服务调用KeyCloak的API来将email_verified属性从false设置为True。

因为web12345是基于RBAC的，那么用户注册后，需要绑定一个role，如何绑定呢？如何更改呢？如何去掉呢？我们可不可以只用KeyCloak的dashboard来完成这些管理呢？pyRBAC项目会告诉你。

## step3，web12345上的用户登录和会话

用户登录web12345的时候，web12345将其重定向到KeyCloak；登陆完成后（经过终端用户授权），web12345就拿到了ID token、access token，然后就拿到了用户的信息（Claims）。web12345拿到ID token和access token之后，按道理来说，下面就是终端用户和web12345的业务往来了。别急，既然是登录，就要涉及登录会话管理了，简单来说就是：

- web12345知道你刚登录上来；
- web12345知道你正在登录期间（也就是会话状态）；
- web12345知道你刚登出。

但是，实现web12345的登录会话也有两种思路：

- 基于session；
- 基于token。

web12345因为是web业务，因此对登录人数、次数、设备、强制一台设备登录有要求。此外，基于token也无法实现登出。所以基于token是不行的，我们选择的思路是：基于token的session:

- 把ID token作为cookie使用，服务端据此实现会话；
- 服务端把ID token维护在redis中，实现服务端的session，用户登出后在redis中清除ID token。
- web12345即使重启，session也不会丢失，鹅妹子嘤。

## step4，web12345上的用户的鉴权

web12345是RBAC的，也就是一个用户有没有权限做一件事情，取决于该用户的role。在设计web12345的时候，我们已经把web服务设计为了RESTful的风格，最起码在这里，用户有没有权限做一件事情，就是用户有没有权限调用一个REST API。web12345服务端是怎么判断出当前用户有没有权限调用一个REST API的呢？相关的信息是每次请求中都从Session里获取呢，还是只使用token中解码出来的信息呢？鉴权是在web12345的本地就完成了呢，还是需要web12345去KeyCloak请求然后由KeyCloak的返回值决定呢？。pyRBAC项目会告诉你。

# 场景二：REST API调用
这个场景就简单多了，这10个REST API就是OAuth2.0中的Resource servers。首先这些Resource servers不需要实现登录会话，其次也不需要实现OIDC规范。并且，这个场景又和OAuth2.0不一样，因为这个场景下没有resource owner。它只需要做到以下几点：

- API付费用户使用Appkey和AppSecret从KeyCloak换取access token（一定是KeyCloak吗？）；
- Resource servers可以根据access token拿到API付费用户的信息（计费）；
- Resource servers可以根据access token确定API付费用户是否用权限访问该API（鉴权）。

Resource servers通常要依据某些信息，来决定是否允许当前的请求访问某些被保护的资源。对于RESTful的resource servers来说（就像这个场景中的10个REST API），这些信息是包含在access token（RTP）里的，并且以bearer token的形式在每次的REST请求中都要携带。

我们参考了下面这篇文章提到的OAuth2.0中的Grant Type: Client Credential 流程：

Gemfield：OAuth2.0、OpenID Connect和JWT
​zhuanlan.zhihu.com/p/351693888
且把这个流程中的Client当作API付费用户：

- Client（“API付费用户”）使用自己的client id和client secret去请求Authorization Server（KeyCloak），获得Access Token；client id和client secret是管理员在KeyCloak注册生成并且颁发给Client（“API付费用户”）的，有时也叫App ID 和 App Secret；
- Client（“API付费用户”）现在可以使用Access Token来向Resource Server（10个REST API）发起一些API调用了；
- Resource Server（10个REST API）从Access Token中解析出API付费用户的信息（神奇吧，OIDC规范下的ID Token的信息居然可以包含在access token中？）；
- Resource Server（10个REST API）从Access Token中解析出API付费用户绑定的role、permission，然后和当前的REST API进行比较（这一步是让鉴权在rest服务本地完成，不用请求KeyCloak），以此确定该请求是否有权限。

更多的细节，请参考pyRBAC项目。

# pyRBAC
最后，我们的做法被封装成了一个轻量级的python库：pyRBAC。它开源在了

DeepVAC/pyRBAC
​github.com/DeepVAC/pyRBAC

这个项目的代码将会在最近发布。
