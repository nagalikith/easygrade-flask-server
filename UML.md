```mermaid
classDiagram
    class App {
        +run()
    }
    
    class API {
        +AssignmentAPI
        +ExecCodeAPI
        +SectionAPI
        +UserAPI
    }
    
    class PyLib {
        +AWSRel
        +DBLibs
        +FileOpLibs
        +HelperLibs
        +RunLang
        +form_helper
        +gen_hex
        +handle_fileop
        +hex_rel
        +user_auth
    }
    
    class AWSRel {
        +S3Rel
    }
    
    class DBLibs {
        +DBConnect
        +DBInit
        +DBSchema
        +DBSecOp
        +DBUserOp
        +TestDB
    }
    
    class FileOpLibs {
        +AssnFileOp
        +FileOpHelper
        +SubmFileOp
    }
    
    class HelperLibs {
        +ImportHelper
        +ModEnvVars
    }
    
    class RunLang {
        +Lang
        +LangC
        +LangCPP
        +LangPython
        +LangRuby
        +RunCode
    }
    
    class Routes {
        +RouAssnRel
        +RouteExecCode
        +RouteSecRel
        +RouteUserRel
    }
    
    App --> API
    App --> PyLib
    App --> Routes
    PyLib --> AWSRel
    PyLib --> DBLibs
    PyLib --> FileOpLibs
    PyLib --> HelperLibs
    PyLib --> RunLang