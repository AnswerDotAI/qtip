import qtip_kernels
import torch

kernels = [
    (1024, 1, 3072, 4),
    (8192, 1, 3072, 4),
    (3072, 1, 8192, 4),
    (3072, 1, 3072, 4),
    (53248, 1, 16384, 2),
    (53248, 1, 16384, 3),
    (53248, 1, 16384, 4),
    (16384, 1, 53248, 2),
    (16384, 1, 53248, 3),
    (16384, 1, 53248, 4),
    (1024, 1, 16384, 2),
    (1024, 1, 16384, 3),
    (1024, 1, 16384, 4),
    (16384, 1, 16384, 2),
    (16384, 1, 16384, 3),
    (16384, 1, 16384, 4),
    (4096, 1, 14336, 2),
    (4096, 1, 14336, 3),
    (4096, 1, 14336, 4),
    (14336, 1, 4096, 2),
    (14336, 1, 4096, 3),
    (14336, 1, 4096, 4),
    (1024, 1, 4096, 2),
    (1024, 1, 4096, 3),
    (1024, 1, 4096, 4),
    (4096, 1, 4096, 2),
    (4096, 1, 11008, 2),
    (11008, 1, 4096, 2),
    (12288, 1, 4096, 2),
    (22016, 1, 4096, 2),
    (8192, 1, 8192, 2),
    (10240, 1, 8192, 2),
    (10240, 1, 8192, 3),
    (10240, 1, 8192, 4),
    (57344, 1, 8192, 2),
    (57344, 1, 8192, 3),
    (57344, 1, 8192, 4),
    (8192, 1, 1024, 2),
    (8192, 1, 28672, 2),
    (28672, 1, 8192, 2),
    (1024, 1, 8192, 2),
    (4096, 1, 4096, 3),
    (4096, 1, 11008, 3),
    (11008, 1, 4096, 3),
    (12288, 1, 4096, 3),
    (22016, 1, 4096, 3),
    (8192, 1, 8192, 3),
    (8192, 1, 1024, 3),
    (8192, 1, 28672, 3),
    (28672, 1, 8192, 3),
    (1024, 1, 8192, 3),
    (4096, 1, 4096, 4),
    (4096, 1, 11008, 4),
    (11008, 1, 4096, 4),
    (12288, 1, 4096, 4),
    (22016, 1, 4096, 4),
    (8192, 1, 8192, 4),
    (8192, 1, 1024, 4),
    (8192, 1, 28672, 4),
    (28672, 1, 8192, 4),
    (1024, 1, 8192, 4),
    (5120, 1, 5120, 3),
    (1024, 1, 3072, 4),
]

kdict = {}
registered_kernels = set()

for m, n, k, bitrate in kernels:
    name = f"quip_lib::decompress_matvec_qtip_{m}_{n}_{k}_{bitrate}"
    if name not in registered_kernels:
        try:
            torch.library.define(
                name,
                "(Tensor compressed, Tensor x, Tensor codebook) -> Tensor")
            registered_kernels.add(name)

            kernel_name = f"qtip_kernels.decompress_matvec_16_9_{bitrate}_1_{m}_{n}_{k}"
            exec(f"""
@torch.library.register_fake("{name}")
def {name}_abstract(
        compressed: torch.Tensor,
        x: torch.Tensor,
        codebook: torch.Tensor) -> torch.Tensor:
    return torch.zeros(1, {m}, dtype=torch.float32, device=x.device)

@torch.library.impl("{name}", "cuda")
def {name}_cuda(
        compressed: torch.Tensor,
        x: torch.Tensor,
        codebook: torch.Tensor) -> torch.Tensor:
    out = torch.zeros(({m}, 1), dtype=torch.float32, device=x.device)
    {kernel_name}(out, compressed.reshape(-1).view(torch.int32), x.to(torch.float16).T, codebook.reshape(-1))
    return out.T
            """)
        except RuntimeError as e:
            if "Duplicate registration" not in str(e):
                raise
