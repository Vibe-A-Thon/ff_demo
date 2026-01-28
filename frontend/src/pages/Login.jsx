import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { Activity, Shield, Lock, Mail, User, AlertTriangle } from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [activeTab, setActiveTab] = useState("login");
  const [loading, setLoading] = useState(false);

  // Login form state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form state
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirmPassword, setRegConfirmPassword] = useState("");
  const [regRole, setRegRole] = useState("analyst");

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!loginEmail || !loginPassword) {
      toast.error("Please fill in all fields");
      return;
    }
    setLoading(true);
    try {
      await login(loginEmail, loginPassword);
      toast.success("Welcome back to Fraud Forge!");
      navigate("/war-room");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!regName || !regEmail || !regPassword || !regConfirmPassword) {
      toast.error("Please fill in all fields");
      return;
    }
    if (regPassword !== regConfirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (regPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    try {
      await register(regEmail, regPassword, regName, regRole);
      toast.success("Account created successfully!");
      navigate("/war-room");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    try {
      // Try to login with demo account, if fails, register it
      try {
        await login("demo@fraudforge.io", "demo123456");
      } catch {
        await register("demo@fraudforge.io", "demo123456", "Demo User", "analyst");
      }
      toast.success("Welcome to Fraud Forge Demo!");
      navigate("/war-room");
    } catch (error) {
      toast.error("Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4" data-testid="login-page">
      {/* Background Pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-red-500/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-blue-500/20 border border-blue-500/30">
              <Activity className="h-8 w-8 text-blue-400" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">Fraud Forge</h1>
          </div>
          <p className="text-muted-foreground">
            Enterprise Fraud Detection Simulation Platform
          </p>
        </div>

        <Card className="border-border bg-card/50 backdrop-blur">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-xl">Access Control</CardTitle>
            <CardDescription>
              Sign in to access the War Room and fraud simulations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="login" data-testid="login-tab">
                  <Lock className="h-4 w-4 mr-2" />
                  Sign In
                </TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab">
                  <User className="h-4 w-4 mr-2" />
                  Register
                </TabsTrigger>
              </TabsList>

              {/* Login Tab */}
              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="analyst@bank.com"
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        className="pl-10"
                        data-testid="login-email-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="••••••••"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        className="pl-10"
                        data-testid="login-password-input"
                      />
                    </div>
                  </div>
                  <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit-btn">
                    {loading ? "Signing in..." : "Sign In"}
                  </Button>
                </form>
              </TabsContent>

              {/* Register Tab */}
              <TabsContent value="register">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reg-name">Full Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="reg-name"
                        placeholder="John Smith"
                        value={regName}
                        onChange={(e) => setRegName(e.target.value)}
                        className="pl-10"
                        data-testid="register-name-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="reg-email"
                        type="email"
                        placeholder="analyst@bank.com"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        className="pl-10"
                        data-testid="register-email-input"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="reg-password">Password</Label>
                      <Input
                        id="reg-password"
                        type="password"
                        placeholder="••••••••"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        data-testid="register-password-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="reg-confirm">Confirm</Label>
                      <Input
                        id="reg-confirm"
                        type="password"
                        placeholder="••••••••"
                        value={regConfirmPassword}
                        onChange={(e) => setRegConfirmPassword(e.target.value)}
                        data-testid="register-confirm-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Select value={regRole} onValueChange={setRegRole}>
                      <SelectTrigger data-testid="register-role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="analyst">Fraud Analyst</SelectItem>
                        <SelectItem value="engineer">Security Engineer</SelectItem>
                        <SelectItem value="compliance">Compliance Officer</SelectItem>
                        <SelectItem value="admin">Administrator</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit-btn">
                    {loading ? "Creating account..." : "Create Account"}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or</span>
              </div>
            </div>

            {/* Demo Login */}
            <Button
              variant="outline"
              className="w-full"
              onClick={handleDemoLogin}
              disabled={loading}
              data-testid="demo-login-btn"
            >
              <Shield className="h-4 w-4 mr-2" />
              Enter Demo Mode
            </Button>

            {/* Security Notice */}
            <div className="mt-6 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground">
                  This system is for authorized personnel only. All actions are logged and audited 
                  for compliance with banking regulations.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground mt-6">
          Fraud Forge v1.0 • Enterprise Fraud Detection Platform
        </p>
      </div>
    </div>
  );
};

export default Login;
