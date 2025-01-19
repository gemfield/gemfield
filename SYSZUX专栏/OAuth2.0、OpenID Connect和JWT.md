# 背景
从最早的互联网时代开始，人们在使用各种bbs或者其它web应用时，就面临着这样两个基础问题：

- 如何证明你是你？也就是如何身份验证？
- 你在A上的权利，如何授权一部分给B？也就是如何授权鉴权？
Gemfield还年轻的时候，互联网应用还非常简单，回答这两个问题的答案分别是：

- 密码；
- 密码。
但是这样做副作用很大：不安全、麻烦、不灵活。于是，为了克服这些问题，围绕着授权鉴权(authorization)和身份验证(authentication)诞生了很多规范和协议。本文中Gemfield将只讨论最主流的最新的规范和协议：OAuth2.0、OpenID Connect、JWT。其中：

- OAuth 2.0是关于授权鉴权的；
- OpenID Connect是关于身份验证和授权鉴权的，和OpenID很像是吧。OpenID是关于身份验证的（已经过时了，本文不讨论）；
- JWT是OAuth 2.0中的access token、OpenID Connect中的access token和id token使用的格式。
关于上述第2点，OpenID 1.0 和OpenID 2.0 是关于身份验证的老旧规范，openid团队本来希望用户使用openid来进行身份验证，然而一些用户转而使用OAuth 2.0去进行身份验证（注意就是身份验证，不是授权），而后使用OAuth2.0进行身份验证的趋势越来越流行。Openid团队不得不承认用户更喜欢OAuth2.0，所以这些人转而设计了一个新的规范：OpenID Connect（也叫OIDC），这个规范基于OAuth2.0进行了小幅扩展。

所有这些新规范、新协议的核心理念都是：用户把自己的用户名/密码托付给一个可信任的授权中心（比如CivilNet、谷歌、支付宝、微信等），而不是给世界上诸多的成千上万的Web和App。然后，那些成千上万的Web和App转而来向CivilNet、谷歌、支付宝、微信来请求用户的信息和授权鉴权。

# 举个例子
假设Gemfield开发了一个“约Gemfield吃饭”的应用，该应用的功能也极为简单：只要用户登录该应用并且点击按钮，那么就有可能约到Gemfield吃饭。虽说功能极为简单，“约Gemfield吃饭”这个应用也要在用户可以点按钮之前做两个事情：

- 身份验证，也就是确定当前操作的人是谁；
- 授权获取用户的芝麻分，想约Gemfield吃饭，最少也得750分的芝麻分吧；
瞧，身份验证和授权真是无所不在。你肯定已经知道了，“约Gemfield吃饭”这个应用将使用支付宝作为可信任授权中心了，别家也没有芝麻分呀。

注意：在这个场景中，支付宝既是Authorization Server，又是Resource Server。当然也有不是这种情况的——这种情况下Resource Server也得非常信任Authorization Server才行。

# OAuth 2.0
名词解释
```
Resource Owner：资源所有者，也就是...你；
Client：一个应用，想以你的名义在你的其它应用上做事情...“约Gemfield吃饭”;
Authorization Server：一个应用，Resource Owner很信任它且在其上面永远拥有个人账户...支付宝；
Resource Server: 一个应用（API或者服务），Client想要代表Resource Owner来使用...支付宝2（用支付宝2表示虽然这里Authorization Server和Resource Server都是支付宝）;
Redirect URI: 一个网址URL，当Resource Owner在Authorization Server上授权了Client后，Authorization Server将会把Resource Owner重定向到的地方，有时也称“Callback URL”;
Authorization Code: Client发送给Authorization Server的临时code，用于交换Access Token;
Access Token: Client和Resource Server交互所使用的令牌，其上所携带的权限本质上来自你，如今又以你的名义在使用; 一般使用的是JWT格式；
Response Type: Client希望从Authorization Server收到的信息的类型，最常见的Response Type是code，也就是Client希望收到一个Authorization Code。
```
适用到“约Gemfield吃饭”App
```
你，Resource Owner，想要允许“约Gemfield吃饭”这个Client去访问你的芝麻分，然后才能做你梦寐以求的事情：和Gemfield吃饭；
Client（“约Gemfield吃饭”） 重定向你的浏览器到 Authorization Server （支付宝），这个请求包含了 Client ID、Redirect URI、Response Type以及一个或多个所需的Scopes。这里的Response Type为code；
Authorization Server（支付宝）验证你是谁，一般会在你的浏览器上弹出登录框（如果还没登录的话）；
Authorization Server（支付宝）给你展示一个授权“约Gemfield吃饭”看芝麻分的按钮，你点击按钮表示同意（也可以拒绝）；
Authorization Server（支付宝）使用Redirect URI重定向回 Client（“约Gemfield吃饭”），并且携带着Authorization Code;
Client（“约Gemfield吃饭”）现在使用Client ID、Client Secret和Authorization Code直接联系Authorization Server （支付宝）(也就是不通过Resource Owner(你)的浏览器)；
Authorization Server（支付宝） 验证Client ID、Client Secret和Authorization Code并向Client（“约Gemfield吃饭”）返回Access Token；
Client（“约Gemfield吃饭”）现在可以使用Access Token来向Resource Server（支付宝2）发起获取芝麻分的API调用了。
```
上面的场景，正是OAuth2.0中Grant Type为Authorization Code的授权流程。除了Authorization Code这种最常见的授权类型外，OAuth2.0还提供了另外3种授权类型：

- Grant Type: Implicit：隐藏式；
- Grant Type: Resource Owner Password Credentials：密码式；
- Grant Type: Client Credential ：凭证式。

# Grant Type: Implicit：隐藏式

和Authorization Code相比，这种类型跳过了获取Authorization Code的步骤，直接获取令牌：
```
你，Resource Owner，想要允许“约Gemfield吃饭”这个Client去访问你的芝麻分，然后才能做你梦寐以求的事情：和Gemfield吃饭；
Client（“约Gemfield吃饭”） 重定向你的浏览器到 Authorization Server （支付宝），这个请求包含了 Client ID、Redirect URI、Response Type以及一个或多个所需的Scopes。这里的Response Type为token；
Authorization Server（支付宝）验证你是谁，一般会在你的浏览器上弹出登录框（如果还没登录的话）；
Authorization Server（支付宝）给你展示一个授权“约Gemfield吃饭”看芝麻分的按钮，你点击按钮表示同意（也可以拒绝）；
Authorization Server（支付宝）使用Redirect URI重定向回 Client（“约Gemfield吃饭”），并且携带着Access Token;
Client（“约Gemfield吃饭”）现在可以使用Access Token来向Resource Server（支付宝2）发起获取芝麻分的API调用了。
```
# Grant Type: Resource Owner Password Credentials：密码式

和前面的类型相比，这种类型需要用户把密码给“约Gemfield吃饭”。所以前提就是用户需要非常信任“约Gemfield吃饭”了，不过...谁又不信任Gemfield呢？
```
你，Resource Owner，想要允许“约Gemfield吃饭”这个Client去访问你的芝麻分，然后才能做你梦寐以求的事情：和Gemfield吃饭；
Client（“约Gemfield吃饭”）要Resource Owner（你）提供其在Authorization Server（支付宝）上的用户名和密码（注意：实际中千万别给！！！这里只是演示！！！虽然我知道你非常信任Gemfield！！！那也别给！！！）；
Client（“约Gemfield吃饭”）以Resource Owner（你）的用户名密码去请求Authorization Server（支付宝），获得Access Token;
Client（“约Gemfield吃饭”）现在可以使用Access Token来向Resource Server（支付宝2）发起获取芝麻分的API调用了。
```
# Grant Type: Client Credential ：凭证式。

这种方式获得的令牌是Client级别的，和用户没什么直接关系。
```
Client（“约Gemfield吃饭”）使用自己的client id和client secret（开发者在支付宝注册时获得的，有时也叫App ID 和 App Secret）去请求Authorization Server（支付宝），获得Access Token;
Client（“约Gemfield吃饭”）现在可以使用Access Token来向Resource Server（支付宝2）发起一些支付宝允许的API调用了。
```
# OpenID Connect (OIDC)
我们知道，传统的登录设计有很多缺点，比如：

- 用户到每个服务上都要经历一遍注册登录验证流程，烦死了；
- 用户的多个注册登录中，注册要不要使用一样的密码？使用不一样的密码吧，用户容易忘记；使用一样的密码吧，有撞库的风险。烦死了；
- 对于像CivilNet这样的组织来说，其有很多应用，如果每个应用都使用不同的用户数据库，那维护工作简直就是灾难，开发工作也是个灾难。烦死了。

为了不被烦死，OpenID connect诞生了（简称为OIDC）。前文我们已经知道，OAuth 2.0 主要是为了授权而设计的，OpenID Connect在其上做了小幅扩展，用来表明当前登录用户（Resource Owner）的信息——这就是要进军身份验证领域了。当 Authorization Server支持OIDC的时候，我们也称它为identity provider(简写为IdP，在OIDC规范中也叫OP)——它向Client提供了当前Resource Onwer的信息。

如此一来，OIDC就打开了一个新的世界，就是一次登录可以用在多个应用上，我们称之为单点登录SSO。前面已经说了OIDC是在OAuth2.0上做的小幅扩展，那么这个扩展到底是什么呢？在OAuth2.0上的扩展就两点：

- 在最早的Client向Authorization Server请求这一步中， Client（“约Gemfield吃饭”） 重定向你的浏览器到 Authorization Server （支付宝），这个请求包含了 Client ID、Redirect URI、Response Type以及一个或多个所需的Scopes；在OIDC中使用了scope=openid、在OIDC中使用了scope=openid、在OIDC中使用了scope=openid，重要的事情说三遍！
- 在最后的Authorization Server向Client返回access token这一步，Authorization Server（支付宝） 验证Client ID、Client Secret和Authorization Code并向Client（“约Gemfield吃饭”）返回Access Token；在OIDC中，返回Access Token和ID Token、在OIDC中，返回Access Token和ID Token、在OIDC中，返回Access Token和ID Token，重要的事情还是说三遍！
OIDC自己也定义了一些术语，主要有：

- EU：End User：用户。
- RP：Relying Party ，相当于Client；
- OP：OpenID Provider，IdP，比如keycloak，比如CivilNet、谷歌之类的；
- ID Token：JWT格式的数据，包含用户身份信息。
- UserInfo Endpoint：获取用户信息的API，当RP使用Access Token访问时，返回用户的信息。
还记得OAuth 2.0有四种流程吗？OIDC中获取ID token的流程主要使用了Authorisation code flow 和 Implicit flow 。简化一下就是：

- RP发送一个认证请求给OP；
- OP对EU进行身份认证，然后EU授权RP；
- OP返回ID Token和Access Token给RP；
- RP携带Access Token发送请求到UserInfo EndPoint；
- UserInfo EndPoint返回EU的Claims。
注意，我们借助Keycloak的client mapper功能，可以直接把5步中的Claims放到3步中的ID Token中！

ID token除了用于表明用户信息外，还可以：

- 无状态会话，将ID token作为cookie使用，可以实现一个轻量级的无状态会话。 当ID token中的iat已经过了一段预先定义好的时间后，应用可以使用prompt=none的方式向OP（OpenID Provider，比如keycloak，比如CivilNet、谷歌之类的）请求一个新的；
- 送给三方，把这个ID Token传给第三方使用；
- Token交换 ，通过OAuth 2.0 authorisation服务的token endpoint(draft-ietf-oauth-token-exchange-12)，ID token可以交换access token 。对应现实世界中的一个例子就是，你在酒店办理入住时通过身份证件获得房间钥匙。
和Access token一样，这个ID TOKEN的格式也是JWT（JSON Web Token）。使用一些JWT库可以进行解码和验证，从而获得JWT中的信息。对于ID TOKEN来说，解码后这里面你会看到payload中包含了你的ID、name、有效时间之类的：
```
{
  "exp": 1614187991,
  "iat": 1614151991,
  "auth_time": 0,
  "jti": "5fb2695c-7c50-44a9-abe4-5a625f249e86",
  "iss": "http://ai3.gemfield.org:8080/auth/realms/gemfield",
  "aud": "DeepVAC",
  "sub": "b0433805-a520-43e0-b37a-00bd157a64c2",
  "typ": "ID",
  "azp": "DeepVAC",
  "session_state": "fe74aea4-e276-4019-9cb8-552f024d6e45",
  "at_hash": "OvsLiONqrRPSvdu-IpOhNQ",
  "acr": "1",
  "email_verified": true,
  "mobile": "176xxxx2021",
  "name": "CivilNet Gemfield",
  "preferred_username": "gemfield",
  "given_name": "Gemfield",
  "family_name": "CivilNet",
  "email": "gemfield@civilnet.cn"
}
```
这种数据在JWT规范中称之为claims。如果你使用的OIDC实现是keycloak的话，结合keycloak中的client的mapper功能，你可以往ID TOKEN中添加你想要的claim，比如上述的mobile字段就是这样添加的——多么有趣呀。

# JWT
JSON Web Token的缩写，在其之上：

- JWT可以签名，使用的是JSON Web Signatures (JWS, RFC 75156 )；
- JWT可以加密，使用的是JSON Web Encryption (JWE, RFC 75167 )。
在OIDC中，我们一般用的就是签名后的JWT，下文使用JWT/JWS来表示。JWT就是一组字符串，未被JWE（加密）的JWT/JWS由圆点分割成三部分：header、payload、签名区。

## JWT Header

每个JWT都包含了一个header，header里一般包含有算法、类型等字段。比如：
```
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "3xlPpbbfY4Mdmr3QCPREUOKQ88Z2IJND3zdj2HXsiys"
}
```
## JWT payload

包含了各种claims，其中有特殊含义的（类似编程语言中的关键字）的claim称之为registered claims：

- iss: from the word issuer. A case-sensitive string or URI that uniquely identifies the party that issued the JWT. Its interpretation is application specific (there is no central authority managing issuers).
- sub: from the word subject. A case-sensitive string or URI that uniquely identifies the party that this JWT carries information about. In other words, the claims contained in this JWT are statements about this party. The JWT spec specifies that this claim must be unique in the context of the issuer or, in cases where that is not possible, globally unique. Handling of this claim is application specific.
- aud: from the word audience. Either a single case-sensitive string or URI or an array of such values that uniquely identify the intended recipients of this JWT. In other words, when this claim is present, the party reading the data in this JWT must find itself in the aud claim or disregard the data contained in the JWT. As in the case of the iss and sub claims, this claim is application specific.
- exp: from the word expiration (time). A number representing a specific date and time in the format “seconds since epoch” as defined by POSIX6 . This claims sets the exact moment from which this JWT is considered invalid. Some implementations may allow for a certain skew between clocks (by considering this JWT to be valid for a few minutes after the expiration date).
- nbf: from not before (time). The opposite of the exp claim. A number representing a specific date and time in the format “seconds since epoch” as defined by POSIX7 . This claim sets the exact moment from which this JWT is considered valid. The current time and date must be equal to or later than this date and time. Some implementations may allow for a certain skew.
- iat: from issued at (time). A number representing a specific date and time (in the same format as exp and nbf) at which this JWT was issued.
- jti: from JWT ID. A string representing a unique identifier for this JWT. This claim may be used to differentiate JWTs with other similar content (preventing replays, for instance). It is up to the implementation to guarantee uniqueness.
所有的名字都是三个字母，故意这么短可以让JWT变得更小，节约资源，也方便解析。比如下面就是一个access token解码后的payload：
```
{
  "exp": 1614246106,
  "iat": 1613814106,
  "jti": "01768805-f1f6-46b7-afa5-4b14de03cc71",
  "iss": "http://ai1.gemfield.org:8080/auth/realms/gemfield",
  "sub": "f2b1a34a-6f88-4af7-b0a6-3f781ece380d",
  "typ": "Bearer",
  "azp": "broker",
  "session_state": "706165aa-d1b0-4021-b0d5-a8b021852ba7",
  "acr": "1",
  "resource_access": {
    "broker": {
      "roles": [
        "/api/v1/orders/gemfield/edit",
        "/api/v1/orders/gemfield/delete",
        "/api/v1/users/civilnet/edit",
        "/api/v1/users/civilnet/create",
      ]
    }
  },
  "scope": "profile email",
  "email_verified": false,
  "preferred_username": "gemfield@civilnet.cn",
  "email": "gemfield@civilnet.cn"
}
```
所有不是registered claims的claim称之为private claims或 public claims：

- Private claims: 开发人员自行定义的；
- Public claims: 要么是注册在IANA JSON Web Token Claims registry8上的，要么是名字有类似于命名空间的前缀用来预防名字冲突的。
实践中，几乎所有的claims都是registered claims或者private claims。

## 编码和解码一个未签名的JWT

编码一个JWT的步骤如下：

- jwt header使用UTF-8表示，然后使用Base64-URL算法编码header，去除结尾的等号；
- jwt payload使用UTF-8表示，然后使用Base64-URL算法编码payload，去除结尾的等号；
- 使用“.”将jwt header和jwt payload连接起来。
如下图所示：
![Image](https://github.com/user-attachments/assets/fe9dd138-0414-415c-9a76-1c406580c068)

相应的解码一个JWT的步骤如下：

- 找到“.”字符，取其前面的内容，使用Base64-URL算法解码，结果就是JWT header；
- 取“.”字符后面的内容，使用Base64-URL算法解码，结果就是JWT payload。

# 编码和解码一个签名的JWT/JWS

如下图所示：
![Image](https://github.com/user-attachments/assets/91df6c6d-5af7-45c2-9441-4c6e8301aeb2)

主要就是签名部分使用了签名算法，这里的算法主要有对称加密和非对称加密：

- 对称加密，生产者和消费者需要共享一个secret；
- 非对称加密，生产者和消费者只需要共享public key即可，private key是不外露的。

JSON Web Encryption（JWE）就不说了，我们的环境中不用。

# JWT的其它形式
在OIDC规范中，基于JWT的扩展还产生了两种新的JWT：PAT和RPT。

## 1，Protection API Access Token (PAT)

为了介绍PAT，请允许Gemfield引入OIDC的一个著名实现：keycloak。在Keycloak中，资源的管理是通过Keycloak Administration Console 或者Protection API来完成的，其中Protection API就是UMA-compliant的REST API，从而可以远端对资源进行管理，包括：

- 资源管理（Resource Management）；
- 权限管理（Permission Management）；
- 策略API（Policy API）。

先暂停下，上面的UMA-compliant是什么意思？就是符合User-Managed Access (UMA) 2.0协议的意思。这个协议定义了（注意OIDC中的术语）：

- 使得end user可以向authorization server中引入新的resource的方法；
- 一组策略，用来监管对resource的访问；
- RP如何提供claims，从而满足访问resource的策略要求。

再回到我们的keycloak场景中，如果要使用Protection API，请求的时候就必须携带一种新的access token，没错，我们称之为protection API token (PAT)。 在UMA规范中，一个PAT就是含有scope是uma_protection的access token。有了PAT，我们就可以通过Protection API来：

- 创建一个resource；
- 更新一个resource；
- 为一个resouce定义一个新的owner；
- 创建一个permission ticket；
- 等等。

在OIDC的规范中，PAT的payload中必须包含如下字段：

- iss，The issuer URL of the authorization server；
- aud，An array containing the URL of the introspection endpoint and the URL of the resource set registration endpoint；
- sub，The issuer-specific identifier of the user that authorized the PAT；
- azp，The client identifier of the protected resource.
## 2，Requesting Party Token (RPT)

还是引入我们的keycloak，在keycloak中，我们的access token默认都是签名的JWT（也就是JWT + JWS），称之为Requesting Party Token ，缩写为RPT。

在OIDC的规范中，RPT的payload中必须包含如下字段：

- iss，The issuer URL of the authorization server；
- aud，An array of resource identifiers where this token can be used；
- sub，The issuer-specific identifier of the user that authorized the RPT (the resource owner)；
- azp，The client identifier of the authorized client.
