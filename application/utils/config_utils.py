def get_config(idx):
    match idx:
        case 1:
            return {
                'idx': 1,
                'dataset_name': 'l',           # 'm' or 'l'
                'assets': {'range': 500, '#partitions': 10},
                # 'thresholds': [0.3, 0.4, 0.5, 0.6, 0.7],
                'thresholds': [0.4],
                # 'deltas': [0.55, 0.6, 0.65, 0.7, 0.75],
                'deltas': [0.6],
                'R_var': 0.01,
                'gamma': 0.05,
                'time_limit': 7200,
                'dist_constr': 'star',       # 'clique' or 'star'
                'valid_day_constr': False,
                'delta_constr': 'inequality',   # 'equality' or 'inequality
                'iterative_warmstart': True
            }
        
        case 2:
            return {
                'idx': 2,
                'dataset_name': 'l',           # 'm' or 'l'
                'assets': {'range': 500, '#partitions': 10},
                'thresholds': [0.4],
                'deltas': [0.05],
                'R_var': -0.01,
                'gamma': 0.05,
                'time_limit': 7200,
                'dist_constr': 'star',       # 'clique' or 'star'
                'valid_day_constr': False,
                'delta_constr': 'inequality',   # 'equality' or 'inequality
                'iterative_warmstart': True
            }
        
        case 3:
            return {
                'idx': 3,
                'dataset_name': 'l',            # 'm' or 'l'
                'assets': {'range': 500, '#partitions': 1},
                'thresholds': [0.4],
                'deltas': [0.6],
                'R_var': 0.01,
                'gamma': 0.05,
                'time_limit': 7200,
                'dist_constr': 'star',          # 'clique' or 'star'
                'valid_day_constr': False,
                'delta_constr': 'inequality',   # 'equality' or 'inequality
                'iterative_warmstart': False
            }