"""
GPU Settings API
Handles GPU configuration and installation
"""

import asyncio
import os
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class GPUManager:
    """Manages GPU detection and installation"""
    
    def __init__(self):
        self.venv_path = Path(os.getenv('VIRTUAL_ENV', 'venv'))
        self.python_exe = self.venv_path / ('Scripts' if platform.system() == 'Windows' else 'bin') / ('python.exe' if platform.system() == 'Windows' else 'python')
        self.pip_exe = self.venv_path / ('Scripts' if platform.system() == 'Windows' else 'bin') / ('pip.exe' if platform.system() == 'Windows' else 'pip')
    
    def get_current_device(self) -> str:
        """Get current compute device"""
        if not TORCH_AVAILABLE:
            return 'cpu'
        
        try:
            if torch.cuda.is_available():
                return 'cuda'
            elif torch.backends.mps.is_available():
                return 'metal'
            else:
                return 'cpu'
        except Exception:
            return 'cpu'
    
    def check_available_gpus(self) -> Dict[str, bool]:
        """Check which GPU backends are available"""
        available = {
            'cuda': False,
            'rocm': False,
            'metal': False
        }
        
        if TORCH_AVAILABLE:
            try:
                available['cuda'] = torch.cuda.is_available()
            except Exception:
                pass
            
            try:
                available['metal'] = torch.backends.mps.is_available()
            except Exception:
                pass
        
        # Check ROCm (AMD)
        try:
            result = subprocess.run(
                ['rocminfo'],
                capture_output=True,
                timeout=5
            )
            available['rocm'] = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return available
    
    async def install_gpu_support(self, gpu_type: str) -> Dict[str, Any]:
        """
        Install GPU support for specified backend
        
        Args:
            gpu_type: 'cuda', 'rocm', 'metal', or 'cpu'
        
        Returns:
            Installation status
        """
        if gpu_type == 'cpu':
            return {
                'status': 'success',
                'message': 'CPU ist bereits als Standard aktiv'
            }
        
        if gpu_type == 'cuda':
            return await self._install_cuda()
        elif gpu_type == 'rocm':
            return await self._install_rocm()
        elif gpu_type == 'metal':
            return await self._install_metal()
        else:
            return {
                'status': 'error',
                'message': f'Unbekannter GPU-Typ: {gpu_type}'
            }
    
    async def _install_cuda(self) -> Dict[str, Any]:
        """Install NVIDIA CUDA support"""
        try:
            # Set environment variables for CUDA
            env = os.environ.copy()
            env['FORCE_CMAKE'] = '1'
            env['CMAKE_ARGS'] = '-DGGML_CUDA=on'
            
            # Run pip install
            process = await asyncio.create_subprocess_exec(
                str(self.pip_exe),
                'install',
                '--force-reinstall',
                '--no-binary',
                'llama-cpp-python',
                'llama-cpp-python',
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minutes timeout
            )
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'message': 'NVIDIA CUDA-Support erfolgreich installiert',
                    'output': stdout.decode()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'CUDA-Installation fehlgeschlagen',
                    'error': stderr.decode()
                }
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'message': 'CUDA-Installation Timeout (>5 Minuten)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'CUDA-Installation Fehler: {str(e)}'
            }
    
    async def _install_rocm(self) -> Dict[str, Any]:
        """Install AMD ROCm support"""
        try:
            env = os.environ.copy()
            env['FORCE_CMAKE'] = '1'
            env['CMAKE_ARGS'] = '-DGGML_HIPBLAS=on'
            
            process = await asyncio.create_subprocess_exec(
                str(self.pip_exe),
                'install',
                '--force-reinstall',
                '--no-binary',
                'llama-cpp-python',
                'llama-cpp-python',
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300
            )
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'message': 'AMD ROCm-Support erfolgreich installiert',
                    'output': stdout.decode()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'ROCm-Installation fehlgeschlagen',
                    'error': stderr.decode()
                }
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'message': 'ROCm-Installation Timeout (>5 Minuten)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'ROCm-Installation Fehler: {str(e)}'
            }
    
    async def _install_metal(self) -> Dict[str, Any]:
        """Install Apple Metal support (macOS only)"""
        if platform.system() != 'Darwin':
            return {
                'status': 'error',
                'message': 'Metal ist nur auf macOS verfügbar'
            }
        
        try:
            env = os.environ.copy()
            env['FORCE_CMAKE'] = '1'
            env['CMAKE_ARGS'] = '-DGGML_METAL=on'
            
            process = await asyncio.create_subprocess_exec(
                str(self.pip_exe),
                'install',
                '--force-reinstall',
                '--no-binary',
                'llama-cpp-python',
                'llama-cpp-python',
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300
            )
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'message': 'Apple Metal-Support erfolgreich installiert',
                    'output': stdout.decode()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Metal-Installation fehlgeschlagen',
                    'error': stderr.decode()
                }
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'message': 'Metal-Installation Timeout (>5 Minuten)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Metal-Installation Fehler: {str(e)}'
            }
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get complete GPU information"""
        available = self.check_available_gpus()
        current = self.get_current_device()
        
        return {
            'current_device': current,
            'available_gpus': [k for k, v in available.items() if v],
            'cuda_available': available['cuda'],
            'rocm_available': available['rocm'],
            'metal_available': available['metal']
        }


# Global GPU manager instance
gpu_manager = GPUManager()