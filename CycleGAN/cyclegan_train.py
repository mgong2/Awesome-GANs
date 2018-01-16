from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import tensorflow as tf
import numpy as np

import sys
import time

import cyclegan_model as cyclegan

sys.path.append('../')
import image_utils as iu
from datasets import Pix2PixDataSet as DataSet


results = {
    'output': './gen_img/',
    'checkpoint': './model/checkpoint',
    'model': './model/CycleGAN-model.ckpt'
}

train_step = {
    'global_steps': 200001,
    'batch_size': 64,
    'logging_step': 2500,
}


def main():
    start_time = time.time()  # Clocking start

    # GPU configure
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True

    with tf.Session(config=config) as s:
        # CycleGAN Model
        model = cyclegan.CycleGAN(s)

        # Initializing
        s.run(tf.global_variables_initializer())

        # Celeb-A DataSet images
        data_set_name = 'vangogh2photo'
        ds = DataSet(input_height=32,
                     input_width=32,
                     input_channel=3,
                     crop_size=32,
                     batch_size=train_step['batch_size'],
                     mode='train',
                     name=data_set_name)

        x_a = tf.transpose(ds.train_images_a, (0, 2, 3, 1))  # N, H, W, C
        x_b = tf.transpose(ds.train_images_b, (0, 2, 3, 1))

        print("[*] %s loaded : took %.8fs" % (data_set_name, time.time() - start_time))
        print("image A shape : ", x_a.shape)
        print("image B shape : ", x_b.shape)

        model.build_cyclegan(x_a, x_b)  # CycleGAN

        """
        sample_x_a = x_a[:model.sample_num]
        sample_x_a = tf.reshape(sample_x_a, [-1] + model.image_shape[1:])
        sample_x_b = x_b[:model.sample_num]
        sample_x_b = tf.reshape(sample_x_b, [-1] + model.image_shape[1:])

        # Export real image
        valid_image_height = model.sample_size
        valid_image_width = model.sample_size

        # Generated image save
        iu.save_images(sample_x_a,
                       size=[valid_image_height, valid_image_width], image_path=results['output'] + 'valid_a.png')
        iu.save_images(sample_x_b,
                       size=[valid_image_height, valid_image_width], image_path=results['output'] + 'valid_b.png')
        """

        threads = tf.train.start_queue_runners(sess=s)
        for global_step in range(train_step['global_steps']):
            for _ in range(model.n_train_critic):
                s.run(model.c_op)

            w, wp, g_loss, cycle_loss, _ = s.run([model.w, model.gp, model.g_loss, model.cycle_loss, model.g_op])

            if global_step % train_step['logging_step'] == 0:
                # Summary
                summary = s.run([model.merged])

                # Print loss
                print("[+] Global Step %08d =>" % global_step,
                      " G loss : {:.8f}".format(g_loss),
                      " Cycle loss : {:.8f}".format(cycle_loss),
                      " w : {:.8f}".format(w),
                      " gp : {:.8f}".format(gp))

                # Summary saver
                model.writer.add_summary(summary, global_step)

                # Training G model with sample image and noise
                samples_a2b = s.run(model.g_a2b)
                samples_b2a = s.run(model.g_b2a)

                # Export image generated by model G
                sample_image_height = model.sample_size
                sample_image_width = model.sample_size
                sample_dir_a2b = results['output'] + 'train_a2b_{0}.png'.format(global_step)
                sample_dir_b2a = results['output'] + 'train_b2a_{0}.png'.format(global_step)

                # Generated image save
                iu.save_images(samples_a2b, [sample_image_height, sample_image_width], sample_dir_a2b)
                iu.save_images(samples_b2a, [sample_image_height, sample_image_width], sample_dir_b2a)

                # Model save
                model.saver.save(s, results['model'], global_step=global_step)

    end_time = time.time() - start_time  # Clocking end

    # Elapsed time
    print("[+] Elapsed time {:.8f}s".format(end_time))

    # Close tf.Session
    s.close()


if __name__ == '__main__':
    main()
